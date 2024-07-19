import argparse
import math
import os
import re
import shutil
import sys

import bpy
import zerolog
from bpy.types import Action, Armature, Camera, Scene
from PIL import Image
from zerolog import log

zerolog.GlobalLogger = log.output(zerolog.ConsoleWriter(out=sys.stderr.buffer))


def _parse_vector3(arg):
    try:
        parts = arg.split(",")
        floats = [float(part) for part in parts]
        if len(floats) != 3:
            raise argparse.ArgumentTypeError(
                "Must provide exactly three floats separated by commas."
            )
        return floats
    except ValueError:
        raise argparse.ArgumentTypeError("All values must be floats.")


def _parse_list(arg):
    return arg.split(",")


parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "--blend-file-path",
    type=str,
    default="files/base.blend",
    help="Blender .blend file path (default %(default)s)",
)
parser.add_argument(
    "--camera-location",
    type=_parse_vector3,
    default=[0.0, -4.0, 1.0],
    help="Camera location (default %(default)s)",
)
parser.add_argument(
    "--camera-rotation-euler",
    type=_parse_vector3,
    default=[1.5708, 0.0, 0.0],
    help="Camera rotation euler XYZ (default %(default)s)",
)
parser.add_argument(
    "--light-angle",
    type=float,
    default=1.5708,
    help="Light angle (default %(default)s)",
)
parser.add_argument(
    "--light-energy",
    type=float,
    default=5.0,
    help="Light energy (intensity) (default %(default)s)",
)
parser.add_argument(
    "--model-file-path",
    type=str,
    default="",
    help="Model file path (default %(default)s)",
)
parser.add_argument(
    "--model-action-name",
    type=str,
    default=None,
    help="Model action name (default %(default)s)",
)
parser.add_argument(
    "--model-armature-name",
    type=str,
    default="Armature",
    help="Model armature name (default %(default)s)",
)
parser.add_argument(
    "--model-excluded-meshes",
    type=_parse_list,
    default=[],
    help="Model meshes to exclude from render (default %(default)s)",
)
parser.add_argument(
    "--model-included-meshes",
    type=_parse_list,
    default=[],
    help="Model meshes to include in render (default %(default)s)",
)
parser.add_argument(
    "--animation-file-path",
    type=str,
    default="",
    help="Model file path (default %(default)s)",
)
parser.add_argument(
    "--animation-armature-name",
    type=str,
    default="Armature.001",
    help="Animation armature name (default %(default)s)",
)
parser.add_argument(
    "--animation-action-name",
    type=str,
    default="mixamo.com|Layer0",
    help="Animation action name (default %(default)s)",
)
parser.add_argument(
    "--renders-output-path",
    type=str,
    default="renders",
    help="Renders output directory path (default %(default)s)",
)
parser.add_argument(
    "--render-one-frame",
    default=False,
    action="store_true",
    help="Render only one frame per direction for testing (default %(default)s)",
)
parser.add_argument(
    "--sprite-sheets-output-path",
    type=str,
    default="sprite_sheets",
    help="Sprite sheets output directory path (default %(default)s)",
)
parser.add_argument(
    "--sprite-sheets-sprite-size",
    type=int,
    default=256,
    help="Sprite sheets sprite size (default %(default)s)",
)
parser.add_argument(
    "--sprite-sheets-size",
    type=int,
    default=4096,
    help="Sprite sheets size (default %(default)s)",
)
parser.add_argument(
    "--sprite-sheets-columns",
    type=int,
    default=16,
    help="Sprite sheets columns (default %(default)s)",
)
parser.add_argument(
    "--print-objects",
    default=False,
    action="store_true",
    help="Print scene objects (default %(default)s)",
)
parser.add_argument(
    "--print-object",
    type=str,
    default=None,
    help="Print an object by name (default %(default)s)",
)
parser.add_argument(
    "--print-actions",
    default=False,
    action="store_true",
    help="Print scene actions (default %(default)s)",
)

args = parser.parse_args()


def print_blender_object_properties(obj: str, prefix: str = "\t"):
    for attribute in dir(obj):
        if not attribute.startswith("__"):
            try:
                value = getattr(obj, attribute)
                if not callable(value):
                    log.info().msg(f"{prefix}{attribute}: {value}")
            except AttributeError:
                log.error().msg(f"{attribute}: <unavailable>")


def print_objects():
    log.info().msg("Objects:")
    for obj in bpy.data.objects:
        log.info().msg(f"\tName: {obj.name}\n\t\tType: {obj.type}")


def print_object_by_name(name: str):
    try:
        obj = bpy.data.objects[name]
        log.info().msg(f"{name}:")
        print_blender_object_properties(obj)
    except KeyError:
        log.fatal().msg(f"Object '{name}' not found")


def print_actions():
    log.info().msg("Actions:")
    for act in bpy.data.actions:
        print_blender_object_properties(act)


def load_scene():
    bpy.ops.wm.open_mainfile(filepath=args.blend_file_path)


def load_model(model_file_path: str) -> Armature:
    bpy.ops.import_scene.fbx(filepath=model_file_path, use_anim=True)
    model_armature_name = args.model_armature_name
    model_armature = None

    if args.model_excluded_meshes:
        for mesh_name in args.model_excluded_meshes:
            if mesh_name in bpy.data.objects:
                obj = bpy.data.objects[mesh_name]
                bpy.data.objects.remove(obj, do_unlink=True)

    try:
        model_armature = bpy.data.objects[model_armature_name]
    except KeyError:
        log.fatal().msg(f"Armature '{model_armature_name}' not found")

    if args.model_excluded_meshes:
        for child in model_armature.children:
            if child.type == "MESH" and child.name in args.model_excluded_meshes:
                bpy.data.objects.remove(child, do_unlink=True)

    if args.model_included_meshes:
        for child in model_armature.children:
            if child.type == "MESH" and child.name not in args.model_included_meshes:
                bpy.data.objects.remove(child, do_unlink=True)

    return model_armature


def load_animation(animation_file_path: str) -> Action:
    bpy.ops.import_scene.fbx(filepath=animation_file_path, use_anim=True)

    action_name = f"{args.animation_armature_name}|{args.animation_action_name}"
    action = None

    try:
        action = bpy.data.actions[action_name]
    except KeyError:
        log.fatal().msg(f"Action '{action_name}' not found")

    return action


# Function to rotate the camera around the armature
def _rotate_camera(camera: Camera, angle: float):
    radius = (
        5  # Adjust this value to change the distance of the camera from the armature
    )
    camera.location.x = radius * math.cos(angle)
    camera.location.y = radius * math.sin(angle)
    camera.location.z = 1  # Adjust this value to change the height of the camera
    camera.rotation_euler = (math.pi / 2, 0, angle + math.pi / 2)


def _clear_folder(folder_path: str):
    os.makedirs(folder_path, exist_ok=True)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log.exc(e).msg(f"failed to delete {file_path}: {e}")


def render(
    scene: Scene, camera: Camera, action: Action, model_name: str, animation_name: str
):
    scene.frame_start = int(action.frame_range[0])
    scene.frame_end = int(action.frame_range[1])

    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end

    if args.render_one_frame:
        scene.frame_end = scene.frame_start
        end_frame = start_frame

    # start at 90 degrees (model facing north)
    initial_angle = 1 * (math.pi / 2)

    # iterate through 8 directions (N, NE, E, SE, S, SW, W, NW)
    for direction in range(8):
        angle = initial_angle + direction * (math.pi / 4)  # 45 degrees in radians
        _rotate_camera(camera, angle)

        for frame in range(start_frame, end_frame + 1):
            bpy.context.scene.frame_set(frame)
            fmt = f"{args.renders_output_path}/{model_name}_{animation_name}_{direction:02d}_{frame:04d}"
            bpy.context.scene.render.filepath = fmt
            bpy.ops.render.render(write_still=True)


def create_sprite_sheets(model_name: str, animation_name: str):
    input_dir = args.renders_output_path
    output_dir = args.sprite_sheets_output_path
    resized_size = (
        args.sprite_sheets_sprite_size,
        args.sprite_sheets_sprite_size,
    )  # new size for the images

    sheet_size = (args.sprite_sheets_size, args.sprite_sheets_size)

    images = [img for img in os.listdir(input_dir) if img.endswith(".png")]

    def sort_key(filename):
        match = re.match(r".*_(\d{2})_(\d{4})\.png", filename)
        if match:
            direction, frame = match.groups()
            return int(direction), int(frame)
        return filename

    images.sort(key=sort_key)

    # number of columns (sprites) per row
    columns = args.sprite_sheets_columns

    for direction in range(8):
        direction_images = [img for img in images if f"_{direction:02d}_" in img]

        sprite_sheet = Image.new("RGBA", sheet_size)

        for index, image_file in enumerate(direction_images):
            img = Image.open(os.path.join(input_dir, image_file))
            img = img.resize(resized_size, Image.Resampling.LANCZOS)
            x = (index % columns) * resized_size[0]
            y = (index // columns) * resized_size[1]
            sprite_sheet.paste(img, (x, y))

        output_file = os.path.join(
            output_dir, f"{model_name}_{animation_name}_{direction:02d}.png"
        )
        sprite_sheet.save(output_file)
        log.info().msg(f"sprite sheet saved as {output_file}")

    log.info().msg("all sprite sheets created successfully!")


def main():
    if args.model_excluded_meshes and args.model_included_meshes:
        log.fatal().msg(
            "Only one of 'model_excluded_meshes' or 'model_included_meshes' should be used"
        )

    load_scene()

    scene = bpy.context.scene
    camera, light = bpy.data.objects.get("Camera", None), bpy.data.objects.get(
        "Light", None
    )

    camera.location = args.camera_location
    camera.rotation_euler = args.camera_rotation_euler

    light.data.angle = args.light_angle
    light.data.energy = args.light_energy

    model_file_path = args.model_file_path
    model_name, _ = os.path.splitext(os.path.basename(model_file_path))

    model_armature = load_model(model_file_path)

    if model_armature.animation_data is None:
        model_armature.animation_data_create()

    animation_file_path = args.animation_file_path

    if animation_file_path == "":
        animation_file_path = model_file_path

    if not args.model_action_name:
        animation_name, _ = os.path.splitext(os.path.basename(animation_file_path))
        action = load_animation(animation_file_path)
    else:
        animation_name = args.model_action_name
        action = bpy.data.actions[
            f"{args.model_armature_name}|{args.model_action_name}"
        ]

    model_armature.animation_data.action = action

    if args.print_object is not None:
        print_object_by_name(args.print_object)
        sys.exit(0)

    if args.print_objects:
        print_objects()
        sys.exit(0)

    if args.print_actions:
        print_actions()
        sys.exit(0)

    _clear_folder(args.renders_output_path)
    render(scene, camera, action, model_name, animation_name)

    log.info().msg("rendering done")

    if args.render_one_frame:
        sys.exit(0)

    _clear_folder(args.sprite_sheets_output_path)
    create_sprite_sheets(model_name, animation_name)

    log.info().msg("done")


if __name__ == "__main__":
    main()

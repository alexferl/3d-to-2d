# 3d-to-2d
A Python script to convert [Mixamo](https://www.mixamo.com) (and others) 3D characters/animations to 2D sprite sheets using [Blender](https://docs.blender.org/api/current/info_quickstart.html) (tested with 3.6.x) and [Pillow](https://python-pillow.org/).
It contains a basic .blend file with a camera (name: `Camera`) and a light (name: `Light`).

> NOTE: This is more an example that should be customized for one's needs versus a ready-to-use tool that just works for many different use cases.
> It works for my needs, but may not work for yours.

## Using
```shell
git clone https://github.com/alexferl/3d-to-2d.git
cd 3d-to-2d
make dev
python convert.py --model-file-path=/path/to/model.fbx --animation-file-path=/path/to/anim.fbx
```

It's possible the default armature and action names won't work for you or if you want to use the script for non-Mixamo models/animations. You can modify them with:
```shell
python convert.py \
    --model-file-path=/path/to/model.fbx \
    --model-armature-name=SomeArmature \
    --animation-file-path=/path/to/anim.fbx \
    --animation-armature-name=AnotherArmature \
    --animation-action-name=SomeAction
```

You can see what objects are present in the scene with:
```shell
python convert.py \
    --model-file-path=/path/to/model.fbx \
    --animation-file-path=/path/to/anim.fbx \
    --print-objects
```

Or actions:
```shell
python convert.py \
    --model-file-path=/path/to/model.fbx \
    --animation-file-path=/path/to/anim.fbx \
    --print-actions
```

### Using with animation(s) included with model
```shell
python convert.py \
    --model-file-path=/path/to/model.fbx \
    --model-armature-name=Rig \
    --model-action-name=Idle
```

### Excluding meshes
```shell
python convert.py \
    --model-excluded-meshes=1H_Axe,2H_Axe
```

### Including meshes
```shell
python convert.py \
    --model-included-meshes=1H_Axe,2H_Axe
```

See which other settings are available with:
```shell
python convert.py --help
```

python convert.py \
    --model-file-path=files/Barbarian.fbx \
    --model-armature-name=Rig \
    --model-action-name=1H_Melee_Attack_Chop \
    --model-excluded-meshes=1H_Axe_Offhand,2H_Axe,Barbarian_Cape,Mug
    --output-suffix=Body

python convert.py \
    --model-file-path=files/Barbarian.fbx \
    --model-armature-name=Rig \
    --model-action-name=Idle \
    --model-included-meshes=Barbarian_ArmLeft \
    --output-suffix=ArmLeft

python convert.py \
    --model-file-path=files/Barbarian.fbx \
    --model-armature-name=Rig \
    --model-action-name=Idle \
    --model-included-meshes=1H_Axe,Barbarian_ArmRight \
    --output-suffix=ArmRight

python convert.py \
    --model-file-path=files/Barbarian.fbx \
    --model-armature-name=Rig \
    --model-action-name=1H_Melee_Attack_Chop \
    --model-included-meshes=1H_Axe \
    --output-suffix=1H_Axe

python convert.py \
    --model-file-path=files/Barbarian.fbx \
    --model-armature-name=Rig \
    --model-action-name=1H_Melee_Attack_Chop \
    --model-included-meshes=Barbarian_Round_Shield \
    --output-suffix=Shield

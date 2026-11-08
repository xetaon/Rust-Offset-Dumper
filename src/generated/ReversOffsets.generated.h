// ===========================================================================
//  ReversOffsets.generated.h - AUTO-GENERATED, DO NOT EDIT
//  source: revers/out/binary_provenance.json
//          (revers/rev_binary.py - static proof from GameAssembly.dll)
//
//  This table is a NAME SOURCE ONLY.  The dumper never takes an offset
//  from here: a slot is written only when the live runtime or the
//  verified .rdata offset table produced it.  The entry just supplies the
//  readable name for a slot whose metadata name is an EAC hash.
// ===========================================================================
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace revers_offsets
{
    struct Field
    {
        const char*    klass;
        std::uint32_t  offset;
        const char*    name;
        const char*    type;
        const char*    kind;   // table | code
    };

    inline constexpr Field fields[] = {
        { "AttackEntity", 0x2F0, "deployDelay", "float", "table" },
        { "AttackEntity", 0x2F4, "repeatDelay", "float", "table" },
        { "AttackEntity", 0x2F8, "animationDelay", "float", "table" },
        { "AttackEntity", 0x2FC, "effectiveRange", "float", "table" },
        { "AttackEntity", 0x300, "npcDamageScale", "float", "table" },
        { "AttackEntity", 0x304, "attackLengthMin", "float", "table" },
        { "AttackEntity", 0x308, "attackLengthMax", "float", "table" },
        { "AttackEntity", 0x30C, "attackSpacing", "float", "table" },
        { "AttackEntity", 0x310, "aiAimSwayOffset", "float", "table" },
        { "AttackEntity", 0x314, "aiAimCone", "float", "table" },
        { "AttackEntity", 0x318, "aiOnlyInRange", "bool", "table" },
        { "AttackEntity", 0x31C, "CloseRangeAddition", "float", "table" },
        { "AttackEntity", 0x320, "MediumRangeAddition", "float", "table" },
        { "AttackEntity", 0x324, "LongRangeAddition", "float", "table" },
        { "AttackEntity", 0x328, "CanUseAtMediumRange", "bool", "table" },
        { "AttackEntity", 0x329, "CanUseAtLongRange", "bool", "table" },
        { "AttackEntity", 0x330, "reloadSounds", "SoundDefinition[]", "table" },
        { "AttackEntity", 0x338, "thirdPersonMeleeSound", "SoundDefinition", "table" },
        { "AttackEntity", 0x340, "recoilCompDelayOverride", "float", "table" },
        { "AttackEntity", 0x344, "wantsRecoilComp", "bool", "table" },
        { "AttackEntity", 0x345, "showCrosshairOnTutorial", "bool", "table" },
        { "AttackEntity", 0x346, "noHeadshots", "bool", "table" },
        { "BasePlayer", 0x2F0, "UserIDString", "string", "code" },
        { "BasePlayer", 0x318, "blueprints", "PlayerBlueprints", "code" },
        { "BasePlayer", 0x358, "lastSentTick", "int", "code" },
        { "BasePlayer", 0x368, "currentTeam", "ulong", "code" },
        { "BasePlayer", 0x398, "modelState", "ModelState", "code" },
        { "BasePlayer", 0x3B8, "voiceRecorder", "PlayerVoiceRecorder", "code" },
        { "BasePlayer", 0x3C8, "eyes", "PlayerEyes", "code" },
        { "BasePlayer", 0x438, "GestureViewModel", "ViewModel", "code" },
        { "BasePlayer", 0x440, "input", "InputState", "code" },
        { "BasePlayer", 0x4C0, "metabolism", "PlayerMetabolism", "code" },
        { "BasePlayer", 0x530, "hidden_CapsuleCollider", "CapsuleCollider", "code" },
        { "BasePlayer", 0x548, "playerRigidbody", "Rigidbody", "code" },
        { "BasePlayer", 0x550, "movement", "PlayerWalkMovement", "code" },
        { "BasePlayer", 0x590, "clActiveItem", "ItemId", "code" },
        { "BasePlayer", 0x5E0, "inventory", "PlayerInventory", "code" },
        { "BasePlayer", 0x5E8, "mounted", "BaseMountable", "code" },
        { "BasePlayer", 0x6D0, "fallDamageEffect", "Effect", "code" },
        { "BasePlayer", 0x6D8, "drownEffect", "Effect", "code" },
        { "BasePlayer", 0x6E0, "playerFlags", "PlayerFlags", "code" },
        { "BasePlayer", 0x6F8, "_displayName", "string", "code" },
        { "BasePlayer", 0x710, "voiceSpeaker", "PlayerVoiceSpeaker", "code" },
        { "BasePlayer", 0x718, "modifiers", "PlayerModifiers", "code" },
        { "BasePlayer", 0x728, "userID", "ulong", "code" },
        { "BasePlayer", 0x748, "playerModel", "PlayerModel", "code" },
        { "PlayerModel", 0x98, "Shoulders", "Transform[]", "code" },
        { "PlayerModel", 0xA0, "AdditionalSpineBones", "Transform[]", "code" },
        { "PlayerModel", 0xB8, "_multiMesh", "SkinnedMultiMesh", "code" },
        { "PlayerModel", 0xD0, "TurnAimSmoothTime", "float", "code" },
        { "PlayerModel", 0xD4, "TurnHead", "TurnSegment", "code" },
        { "PlayerModel", 0xE4, "TurnChest", "TurnSegment", "code" },
        { "PlayerModel", 0xF4, "TurnSpine", "TurnSegment", "code" },
        { "PlayerModel", 0x104, "TurnPelvis", "TurnSegment", "code" },
        { "PlayerModel", 0x114, "TurnChestLowerShare", "float", "code" },
        { "PlayerModel", 0x118, "TurnSpineLowerShare", "float", "code" },
        { "PlayerModel", 0x11C, "TurnHeadLockAngle", "float", "code" },
        { "PlayerModel", 0x120, "TurnHeadSmoothTime", "float", "code" },
        { "PlayerModel", 0x124, "TurnHeadMaxSpeed", "float", "code" },
        { "PlayerModel", 0x128, "TurnHeadAimFadeSpeed", "float", "code" },
        { "PlayerModel", 0x130, "TurnClips", "TurnClipSet", "code" },
        { "PlayerModel", 0x138, "TurnSpeedByBacklog", "AnimationCurve", "code" },
        { "PlayerModel", 0x140, "TurnMoveThreshold", "float", "code" },
        { "PlayerModel", 0x144, "TurnSuppressProceduralLegs", "bool", "code" },
        { "PlayerModel", 0x148, "TurnLegBlendTime", "float", "code" },
        { "PlayerModel", 0x14C, "TurnPelvisEnabled", "bool", "code" },
        { "PlayerModel", 0x150, "TurnPelvisFootPinWeight", "float", "code" },
        { "PlayerModel", 0x154, "TurnArmFadeSpeed", "float", "code" },
        { "PlayerModel", 0x158, "TurnArmFadeWeight", "float", "code" },
        { "PlayerModel", 0x210, "collision", "BoxCollider", "code" },
        { "PlayerModel", 0x218, "censorshipCube", "GameObject", "code" },
        { "PlayerModel", 0x220, "censorshipCubeBreasts", "GameObject", "code" },
        { "PlayerModel", 0x228, "jawBone", "GameObject", "code" },
        { "PlayerModel", 0x230, "neckBone", "GameObject", "code" },
        { "PlayerModel", 0x238, "headBone", "GameObject", "code" },
        { "PlayerModel", 0x240, "leftEye", "GameObject", "code" },
        { "PlayerModel", 0x248, "rightEye", "GameObject", "code" },
        { "PlayerModel", 0x250, "eyeController", "EyeController", "code" },
        { "PlayerModel", 0x258, "blinkController", "EyeBlink", "code" },
        { "PlayerModel", 0x260, "SpineBones", "Transform[]", "code" },
        { "PlayerModel", 0x268, "leftFootBone", "Transform", "code" },
        { "PlayerModel", 0x270, "rightFootBone", "Transform", "code" },
        { "PlayerModel", 0x278, "leftHandPropBone", "Transform", "code" },
        { "PlayerModel", 0x280, "rightHandPropBone", "Transform", "code" },
        { "PlayerModel", 0x288, "rightHandTarget", "Vector3", "code" },
        { "PlayerModel", 0x298, "leftClavicleBone", "Transform", "code" },
        { "PlayerModel", 0x2A0, "isPreview", "bool", "code" },
        { "PlayerModel", 0x2A4, "leftHandTargetPosition", "Vector3", "code" },
        { "PlayerModel", 0x2B0, "leftHandTargetRotation", "Quaternion", "code" },
        { "PlayerModel", 0x2C0, "rightHandTargetPosition", "Vector3", "code" },
        { "PlayerModel", 0x2CC, "rightHandTargetRotation", "Quaternion", "code" },
        { "PlayerModel", 0x2E0, "leftUlnaTwistBone", "Transform", "code" },
        { "PlayerModel", 0x2E8, "rightUlnaTwistBone", "Transform", "code" },
        { "PlayerModel", 0x2F0, "leftHandTwistRelaxWeight", "float", "code" },
        { "PlayerModel", 0x2F4, "rightHandTwistRelaxWeight", "float", "code" },
        { "PlayerModel", 0x2F8, "TwistBones", "PlayerTwistBoneSetup[]", "code" },
        { "PlayerModel", 0x300, "steeringTargetDegrees", "float", "code" },
        { "PlayerModel", 0x304, "playerBoatSteeringTargetDegrees", "float", "code" },
        { "PlayerModel", 0x308, "rightFootTargetPosition", "Vector3", "code" },
        { "PlayerModel", 0x314, "rightFootTargetRotation", "Quaternion", "code" },
        { "PlayerModel", 0x324, "leftFootTargetPosition", "Vector3", "code" },
        { "PlayerModel", 0x330, "leftFootTargetRotation", "Quaternion", "code" },
        { "PlayerModel", 0x340, "legsAnimator", "LegsAnimator", "code" },
        { "PlayerModel", 0x348, "upperBodyMask", "AvatarMask", "code" },
        { "PlayerModel", 0x350, "fullMask", "AvatarMask", "code" },
        { "PlayerModel", 0x358, "CinematicAnimationController", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x360, "DefaultAvatar", "Avatar", "code" },
        { "PlayerModel", 0x368, "CinematicAvatar", "Avatar", "code" },
        { "PlayerModel", 0x370, "DefaultHoldType", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x378, "SleepGesture", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x380, "CrawlToIncapacitatedGesture", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x388, "CrawlToIncapacitatedGestureHandcuff", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x390, "StandToIncapacitatedGesture", "RuntimeAnimatorController", "code" },
        { "PlayerModel", 0x3A0, "MaleSkin", "SkinSetCollection", "code" },
        { "PlayerModel", 0x3A8, "FemaleSkin", "SkinSetCollection", "code" },
        { "PlayerModel", 0x3B0, "MannequinSkin", "SkinSetCollection", "code" },
        { "PlayerModel", 0x3B8, "subsurfaceProfile", "SubsurfaceProfile", "code" },
        { "PlayerModel", 0x3C0, "voiceVolume", "float", "code" },
        { "PlayerModel", 0x3C4, "skinColor", "float", "code" },
        { "PlayerModel", 0x3C8, "skinNumber", "float", "code" },
        { "PlayerModel", 0x3CC, "meshNumber", "float", "code" },
        { "PlayerModel", 0x3D0, "meshSubNumber", "float", "code" },
        { "PlayerModel", 0x3D4, "hairNumber", "float", "code" },
        { "PlayerModel", 0x3D8, "dyeNumber", "float", "code" },
        { "PlayerModel", 0x3DC, "skinType", "int", "code" },
        { "PlayerModel", 0x3E0, "mouthFlapPosRange", "float", "code" },
        { "PlayerModel", 0x3E4, "mouthFlapRotRange", "float", "code" },
        { "PlayerModel", 0x3E8, "mouthSidePosRange", "float", "code" },
        { "PlayerModel", 0x3EC, "mouthSideFrequency", "float", "code" },
        { "PlayerModel", 0x3F0, "ArmMotionWeight", "float", "code" },
        { "PlayerModel", 0x3F4, "ArmGravity", "float", "code" },
        { "PlayerModel", 0x3F8, "ArmGravityByPitch", "AnimationCurve", "code" },
        { "PlayerModel", 0x400, "ArmStiffness", "float", "code" },
        { "PlayerModel", 0x404, "ArmDamping", "float", "code" },
        { "PlayerModel", 0x408, "ArmMotionSpeedLimit", "float", "code" },
        { "PlayerModel", 0x40C, "ArmFlexAngle", "float", "code" },
        { "PlayerModel", 0x410, "ArmFlexByPitch", "AnimationCurve", "code" },
        { "PlayerModel", 0x418, "ArmSpinFadeStart", "float", "code" },
        { "PlayerModel", 0x41C, "ArmSpinFadeEnd", "float", "code" },
        { "PlayerModel", 0x420, "SpineLookUpLimit", "float", "code" },
        { "PlayerModel", 0x424, "SpineTwistClamp", "float", "code" },
        { "PlayerModel", 0x428, "SpineHeadLookWeightVertical", "float", "code" },
        { "PlayerModel", 0x42C, "HeadYawLimit", "float", "code" },
        { "PlayerModel", 0x430, "SpineLowerFollow", "float", "code" },
        { "PlayerModel", 0x434, "SpineFollowSmoothSpeed", "float", "code" },
        { "PlayerModel", 0x438, "movementSounds", "MovementSounds", "code" },
        { "PlayerModel", 0x440, "showSash", "bool", "code" },
        { "PlayerModel", 0x444, "tempPoseType", "int", "code" },
        { "PlayerModel", 0x448, "underwearSkin", "uint", "code" },
        { "PlayerModel", 0x488, "position", "Vector3", "code" },
        { "PlayerModel", 0x678, "animator", "Animator", "code" },
        { "PlayerModel", 0x6D8, "modelState", "ModelState", "code" },
        { "Projectile", 0x28, "initialVelocity", "Vector3", "table" },
        { "Projectile", 0x34, "drag", "float", "table" },
        { "Projectile", 0x38, "gravityModifier", "float", "table" },
        { "Projectile", 0x3C, "thickness", "float", "table" },
        { "Projectile", 0x40, "changeInitialOrientation", "bool", "table" },
        { "Projectile", 0x44, "initialDistance", "float", "table" },
        { "Projectile", 0x48, "initialOrientation", "Vector3", "table" },
        { "Projectile", 0x54, "remainInWorld", "bool", "table" },
        { "Projectile", 0x58, "stickProbability", "float", "table" },
        { "Projectile", 0x5C, "breakProbability", "float", "table" },
        { "Projectile", 0x60, "conditionLoss", "float", "table" },
        { "Projectile", 0x64, "ricochetChance", "float", "table" },
        { "Projectile", 0x68, "penetrationPower", "float", "table" },
        { "Projectile", 0x6C, "canRefract", "bool", "table" },
        { "Projectile", 0x6D, "penetratesVehicles", "bool", "table" },
        { "Projectile", 0x70, "waterIntegrityLoss", "float", "table" },
        { "Projectile", 0x78, "damageProperties", "DamageProperties", "table" },
        { "Projectile", 0x80, "damageDistances", "MinMax", "table" },
        { "Projectile", 0x80, "minMax", "MinMax", "table" },
        { "Projectile", 0x88, "damageMultipliers", "MinMax", "table" },
        { "Projectile", 0x90, "damageTypes", "List<DamageTypeEntry>", "table" },
        { "Projectile", 0x98, "rendererToScale", "ScaleRenderer", "table" },
        { "Projectile", 0x98, "scaleTrailRenderer", "ScaleTrailRenderer", "table" },
        { "Projectile", 0xA0, "firstPersonRenderer", "ScaleRenderer", "table" },
        { "Projectile", 0xA0, "scaleTransform", "ScaleTransform", "table" },
        { "Projectile", 0xA8, "createDecals", "bool", "table" },
        { "Projectile", 0xA9, "doHitEffects", "bool", "table" },
        { "Projectile", 0xB0, "flybySound", "SoundDefinition", "table" },
        { "Projectile", 0xB0, "soundDefinition", "SoundDefinition", "table" },
        { "Projectile", 0xB8, "flybySoundDistance", "float", "table" },
        { "Projectile", 0xC0, "closeFlybySound", "SoundDefinition", "table" },
        { "Projectile", 0xC8, "closeFlybyDistance", "float", "table" },
        { "Projectile", 0xCC, "tumbleSpeed", "float", "table" },
        { "Projectile", 0xD0, "tumbleAxis", "Vector3", "table" },
        { "Projectile", 0xDC, "playDefaultHitEffects", "bool", "table" },
        { "Projectile", 0xE0, "clientEffectData", "CustomEffectData", "table" },
        { "Projectile", 0xE0, "customEffectData", "CustomEffectData", "table" },
        { "Projectile", 0xE8, "clientEffectPrefab", "GameObjectRef", "table" },
        { "Projectile", 0xE8, "gameObjectRef", "GameObjectRef", "table" },
        { "Projectile", 0xF0, "swimScale", "Vector3", "table" },
        { "Projectile", 0xFC, "swimSpeed", "Vector3", "table" },
        { "Projectile", 0x110, "baseProjectile", "BaseProjectile", "table" },
        { "Projectile", 0x118, "projectile", "Projectile", "table" },
        { "Projectile", 0x120, "hidden_ccfe34b7cfa107117310af889ea8338a5bf48454", "HitTest", "table" },
        { "Projectile", 0x140, "maxDistance", "float", "code" },
        { "Projectile", 0x164, "currentVelocity", "Vector3", "code" },
        { "Projectile", 0x170, "currentPosition", "Vector3", "code" },
        { "Projectile", 0x17C, "traveledDistance", "float", "code" },
        { "Projectile", 0x180, "traveledTime", "float", "code" },
        { "Projectile", 0x188, "sentPosition", "Vector3", "code" },
        { "Projectile", 0x194, "previousPosition", "Vector3", "code" },
        { "Projectile", 0x1A0, "previousVelocity", "Vector3", "code" },
        { "Projectile", 0x1AC, "previousTraveledTime", "float", "code" },
        { "Projectile", 0x1E0, "mod", "ItemModProjectile", "table" },
        { "Projectile", 0x1F0, "owner", "BasePlayer", "table" },
    };
    inline constexpr std::size_t field_count =
        sizeof(fields) / sizeof(fields[0]);

    // exact (class, offset) lookup - the slot is already measured live
    inline const Field* Find(const char* klass, std::uint32_t offset)
    {
        if (!klass) return nullptr;
        for (const Field& f : fields)
            if (f.offset == offset && std::strcmp(f.klass, klass) == 0)
                return &f;
        return nullptr;
    }

    inline const char* NameFor(const char* klass, std::uint32_t offset)
    {
        const Field* f = Find(klass, offset);
        return f ? f->name : nullptr;
    }

    inline const char* TypeFor(const char* klass, std::uint32_t offset)
    {
        const Field* f = Find(klass, offset);
        return f ? f->type : nullptr;
    }
} // namespace revers_offsets


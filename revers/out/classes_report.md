# Projectile / AttackEntity / PlayerModel - build 26140533

Cross-check of the requested offsets against every evidence source for this build.

## Projectile

- fields: **55**
- MATCH: **49**
- ALIAS: **6**

| field | offset | type | evidence | status |
|---|---|---|---|---|
| `initialVelocity` | `0x28` | Vector3 | `initialVelocity` | MATCH |
| `drag` | `0x34` | float | `drag` | MATCH |
| `gravityModifier` | `0x38` | float | `gravityModifier` | MATCH |
| `thickness` | `0x3C` | float | `thickness` | MATCH |
| `changeInitialOrientation` | `0x40` | bool | `changeInitialOrientation` | MATCH |
| `initialDistance` | `0x44` | float | `initialDistance` | MATCH |
| `initialOrientation` | `0x48` | Vector3 | `initialOrientation` | MATCH |
| `remainInWorld` | `0x54` | bool | `remainInWorld` | MATCH |
| `stickProbability` | `0x58` | float | `stickProbability` | MATCH |
| `breakProbability` | `0x5C` | float | `breakProbability` | MATCH |
| `conditionLoss` | `0x60` | float | `conditionLoss` | MATCH |
| `ricochetChance` | `0x64` | float | `ricochetChance` | MATCH |
| `penetrationPower` | `0x68` | float | `penetrationPower` | MATCH |
| `canRefract` | `0x6C` | bool | `canRefract` | MATCH |
| `penetratesVehicles` | `0x6D` | bool | `penetratesVehicles` | MATCH |
| `waterIntegrityLoss` | `0x70` | float | `waterIntegrityLoss` | MATCH |
| `damageProperties` | `0x78` | DamageProperties | `damageProperties` | MATCH |
| `damageDistances` | `0x80` | MinMax | `damageDistances` | MATCH |
| `minMax` | `0x80` | MinMax (live alias) | `damageDistances` | ALIAS |
| `damageMultipliers` | `0x88` | MinMax | `damageMultipliers` | MATCH |
| `damageTypes` | `0x90` | List<DamageTypeEntry> | `damageTypes` | MATCH |
| `rendererToScale` | `0x98` | ScaleRenderer | `rendererToScale` | MATCH |
| `scaleTrailRenderer` | `0x98` | ScaleTrailRenderer (live alias) | `rendererToScale` | ALIAS |
| `firstPersonRenderer` | `0xA0` | ScaleRenderer | `firstPersonRenderer` | MATCH |
| `scaleTransform` | `0xA0` | ScaleTransform (live alias) | `firstPersonRenderer` | ALIAS |
| `createDecals` | `0xA8` | bool | `createDecals` | MATCH |
| `doHitEffects` | `0xA9` | bool | `doHitEffects` | MATCH |
| `flybySound` | `0xB0` | SoundDefinition | `flybySound` | MATCH |
| `soundDefinition` | `0xB0` | SoundDefinition (live alias) | `flybySound` | ALIAS |
| `flybySoundDistance` | `0xB8` | float | `flybySoundDistance` | MATCH |
| `closeFlybySound` | `0xC0` | SoundDefinition | `closeFlybySound` | MATCH |
| `closeFlybyDistance` | `0xC8` | float | `closeFlybyDistance` | MATCH |
| `tumbleSpeed` | `0xCC` | float | `tumbleSpeed` | MATCH |
| `tumbleAxis` | `0xD0` | Vector3 | `tumbleAxis` | MATCH |
| `playDefaultHitEffects` | `0xDC` | bool | `playDefaultHitEffects` | MATCH |
| `clientEffectData` | `0xE0` | CustomEffectData | `clientEffectData` | MATCH |
| `customEffectData` | `0xE0` | CustomEffectData (live alias) | `clientEffectData` | ALIAS |
| `clientEffectPrefab` | `0xE8` | GameObjectRef | `clientEffectPrefab` | MATCH |
| `gameObjectRef` | `0xE8` | GameObjectRef (live alias) | `clientEffectPrefab` | ALIAS |
| `swimScale` | `0xF0` | Vector3 | `swimScale` | MATCH |
| `swimSpeed` | `0xFC` | Vector3 | `swimSpeed` | MATCH |
| `baseProjectile` | `0x110` | BaseProjectile | `baseProjectile` | MATCH |
| `projectile` | `0x118` | Projectile | `projectile` | MATCH |
| `hidden_ccfe34b7cfa107117310af889ea8338a5bf48454` | `0x120` | %ccfe34b7 (HitTest) | `hidden_ccfe34b7cfa107117310af889ea8338a5bf48454` | MATCH |
| `maxDistance` | `0x140` | float | `maxDistance` | MATCH |
| `currentVelocity` | `0x164` | Vector3 | `currentVelocity` | MATCH |
| `currentPosition` | `0x170` | Vector3 | `currentPosition` | MATCH |
| `traveledDistance` | `0x17C` | float | `traveledDistance` | MATCH |
| `traveledTime` | `0x180` | float | `traveledTime` | MATCH |
| `sentPosition` | `0x188` | Vector3 | `sentPosition` | MATCH |
| `previousPosition` | `0x194` | Vector3 | `previousPosition` | MATCH |
| `previousVelocity` | `0x1A0` | Vector3 | `previousVelocity` | MATCH |
| `previousTraveledTime` | `0x1AC` | float | `previousTraveledTime` | MATCH |
| `mod` | `0x1E0` | ItemModProjectile | `mod` | MATCH |
| `owner` | `0x1F0` | BasePlayer | `owner` | MATCH |

## AttackEntity

- fields: **22**
- MATCH: **22**

| field | offset | type | evidence | status |
|---|---|---|---|---|
| `deployDelay` | `0x2F0` | float | `deployDelay` | MATCH |
| `repeatDelay` | `0x2F4` | float | `repeatDelay` | MATCH |
| `animationDelay` | `0x2F8` | float | `animationDelay` | MATCH |
| `effectiveRange` | `0x2FC` | float | `effectiveRange` | MATCH |
| `npcDamageScale` | `0x300` | float | `npcDamageScale` | MATCH |
| `attackLengthMin` | `0x304` | float | `attackLengthMin` | MATCH |
| `attackLengthMax` | `0x308` | float | `attackLengthMax` | MATCH |
| `attackSpacing` | `0x30C` | float | `attackSpacing` | MATCH |
| `aiAimSwayOffset` | `0x310` | float | `aiAimSwayOffset` | MATCH |
| `aiAimCone` | `0x314` | float | `aiAimCone` | MATCH |
| `aiOnlyInRange` | `0x318` | bool | `aiOnlyInRange` | MATCH |
| `CloseRangeAddition` | `0x31C` | float | `CloseRangeAddition` | MATCH |
| `MediumRangeAddition` | `0x320` | float | `MediumRangeAddition` | MATCH |
| `LongRangeAddition` | `0x324` | float | `LongRangeAddition` | MATCH |
| `CanUseAtMediumRange` | `0x328` | bool | `CanUseAtMediumRange` | MATCH |
| `CanUseAtLongRange` | `0x329` | bool | `CanUseAtLongRange` | MATCH |
| `reloadSounds` | `0x330` | SoundDefinition[] | `reloadSounds` | MATCH |
| `thirdPersonMeleeSound` | `0x338` | SoundDefinition | `thirdPersonMeleeSound` | MATCH |
| `recoilCompDelayOverride` | `0x340` | float | `recoilCompDelayOverride` | MATCH |
| `wantsRecoilComp` | `0x344` | bool | `wantsRecoilComp` | MATCH |
| `showCrosshairOnTutorial` | `0x345` | bool | `showCrosshairOnTutorial` | MATCH |
| `noHeadshots` | `0x346` | bool | `noHeadshots` | MATCH |

## PlayerModel

- fields: **106**
- MATCH: **106**

| field | offset | type | evidence | status |
|---|---|---|---|---|
| `Shoulders` | `0x98` | Transform[] | `Shoulders` | MATCH |
| `AdditionalSpineBones` | `0xA0` | Transform[] | `AdditionalSpineBones` | MATCH |
| `_multiMesh` | `0xB8` | SkinnedMultiMesh | `_multiMesh` | MATCH |
| `TurnAimSmoothTime` | `0xD0` | float | `TurnAimSmoothTime` | MATCH |
| `TurnHead` | `0xD4` | TurnSegment | `TurnHead` | MATCH |
| `TurnChest` | `0xE4` | TurnSegment | `TurnChest` | MATCH |
| `TurnSpine` | `0xF4` | TurnSegment | `TurnSpine` | MATCH |
| `TurnPelvis` | `0x104` | TurnSegment | `TurnPelvis` | MATCH |
| `TurnChestLowerShare` | `0x114` | float | `TurnChestLowerShare` | MATCH |
| `TurnSpineLowerShare` | `0x118` | float | `TurnSpineLowerShare` | MATCH |
| `TurnHeadLockAngle` | `0x11C` | float | `TurnHeadLockAngle` | MATCH |
| `TurnHeadSmoothTime` | `0x120` | float | `TurnHeadSmoothTime` | MATCH |
| `TurnHeadMaxSpeed` | `0x124` | float | `TurnHeadMaxSpeed` | MATCH |
| `TurnHeadAimFadeSpeed` | `0x128` | float | `TurnHeadAimFadeSpeed` | MATCH |
| `TurnClips` | `0x130` | TurnClipSet | `TurnClips` | MATCH |
| `TurnSpeedByBacklog` | `0x138` | AnimationCurve | `TurnSpeedByBacklog` | MATCH |
| `TurnMoveThreshold` | `0x140` | float | `TurnMoveThreshold` | MATCH |
| `TurnSuppressProceduralLegs` | `0x144` | bool | `TurnSuppressProceduralLegs` | MATCH |
| `TurnLegBlendTime` | `0x148` | float | `TurnLegBlendTime` | MATCH |
| `TurnPelvisEnabled` | `0x14C` | bool | `TurnPelvisEnabled` | MATCH |
| `TurnPelvisFootPinWeight` | `0x150` | float | `TurnPelvisFootPinWeight` | MATCH |
| `TurnArmFadeSpeed` | `0x154` | float | `TurnArmFadeSpeed` | MATCH |
| `TurnArmFadeWeight` | `0x158` | float | `TurnArmFadeWeight` | MATCH |
| `collision` | `0x210` | BoxCollider | `collision` | MATCH |
| `censorshipCube` | `0x218` | GameObject | `censorshipCube` | MATCH |
| `censorshipCubeBreasts` | `0x220` | GameObject | `censorshipCubeBreasts` | MATCH |
| `jawBone` | `0x228` | GameObject | `jawBone` | MATCH |
| `neckBone` | `0x230` | GameObject | `neckBone` | MATCH |
| `headBone` | `0x238` | GameObject | `headBone` | MATCH |
| `leftEye` | `0x240` | GameObject | `leftEye` | MATCH |
| `rightEye` | `0x248` | GameObject | `rightEye` | MATCH |
| `eyeController` | `0x250` | EyeController | `eyeController` | MATCH |
| `blinkController` | `0x258` | EyeBlink | `blinkController` | MATCH |
| `SpineBones` | `0x260` | Transform[] | `SpineBones` | MATCH |
| `leftFootBone` | `0x268` | Transform | `leftFootBone` | MATCH |
| `rightFootBone` | `0x270` | Transform | `rightFootBone` | MATCH |
| `leftHandPropBone` | `0x278` | Transform | `leftHandPropBone` | MATCH |
| `rightHandPropBone` | `0x280` | Transform | `rightHandPropBone` | MATCH |
| `rightHandTarget` | `0x288` | Vector3 | `rightHandTarget` | MATCH |
| `leftClavicleBone` | `0x298` | Transform | `leftClavicleBone` | MATCH |
| `isPreview` | `0x2A0` | bool | `isPreview` | MATCH |
| `leftHandTargetPosition` | `0x2A4` | Vector3 | `leftHandTargetPosition` | MATCH |
| `leftHandTargetRotation` | `0x2B0` | Quaternion | `leftHandTargetRotation` | MATCH |
| `rightHandTargetPosition` | `0x2C0` | Vector3 | `rightHandTargetPosition` | MATCH |
| `rightHandTargetRotation` | `0x2CC` | Quaternion | `rightHandTargetRotation` | MATCH |
| `leftUlnaTwistBone` | `0x2E0` | Transform | `leftUlnaTwistBone` | MATCH |
| `rightUlnaTwistBone` | `0x2E8` | Transform | `rightUlnaTwistBone` | MATCH |
| `leftHandTwistRelaxWeight` | `0x2F0` | float | `leftHandTwistRelaxWeight` | MATCH |
| `rightHandTwistRelaxWeight` | `0x2F4` | float | `rightHandTwistRelaxWeight` | MATCH |
| `TwistBones` | `0x2F8` | PlayerTwistBoneSetup[] | `TwistBones` | MATCH |
| `steeringTargetDegrees` | `0x300` | float | `steeringTargetDegrees` | MATCH |
| `playerBoatSteeringTargetDegrees` | `0x304` | float | `playerBoatSteeringTargetDegrees` | MATCH |
| `rightFootTargetPosition` | `0x308` | Vector3 | `rightFootTargetPosition` | MATCH |
| `rightFootTargetRotation` | `0x314` | Quaternion | `rightFootTargetRotation` | MATCH |
| `leftFootTargetPosition` | `0x324` | Vector3 | `leftFootTargetPosition` | MATCH |
| `leftFootTargetRotation` | `0x330` | Quaternion | `leftFootTargetRotation` | MATCH |
| `legsAnimator` | `0x340` | LegsAnimator | `legsAnimator` | MATCH |
| `upperBodyMask` | `0x348` | AvatarMask | `upperBodyMask` | MATCH |
| `fullMask` | `0x350` | AvatarMask | `fullMask` | MATCH |
| `CinematicAnimationController` | `0x358` | RuntimeAnimatorController | `CinematicAnimationController` | MATCH |
| `DefaultAvatar` | `0x360` | Avatar | `DefaultAvatar` | MATCH |
| `CinematicAvatar` | `0x368` | Avatar | `CinematicAvatar` | MATCH |
| `DefaultHoldType` | `0x370` | RuntimeAnimatorController | `DefaultHoldType` | MATCH |
| `SleepGesture` | `0x378` | RuntimeAnimatorController | `SleepGesture` | MATCH |
| `CrawlToIncapacitatedGesture` | `0x380` | RuntimeAnimatorController | `CrawlToIncapacitatedGesture` | MATCH |
| `CrawlToIncapacitatedGestureHandcuff` | `0x388` | RuntimeAnimatorController | `CrawlToIncapacitatedGestureHandcuff` | MATCH |
| `StandToIncapacitatedGesture` | `0x390` | RuntimeAnimatorController | `StandToIncapacitatedGesture` | MATCH |
| `MaleSkin` | `0x3A0` | SkinSetCollection | `MaleSkin` | MATCH |
| `FemaleSkin` | `0x3A8` | SkinSetCollection | `FemaleSkin` | MATCH |
| `MannequinSkin` | `0x3B0` | SkinSetCollection | `MannequinSkin` | MATCH |
| `subsurfaceProfile` | `0x3B8` | SubsurfaceProfile | `subsurfaceProfile` | MATCH |
| `voiceVolume` | `0x3C0` | float | `voiceVolume` | MATCH |
| `skinColor` | `0x3C4` | float | `skinColor` | MATCH |
| `skinNumber` | `0x3C8` | float | `skinNumber` | MATCH |
| `meshNumber` | `0x3CC` | float | `meshNumber` | MATCH |
| `meshSubNumber` | `0x3D0` | float | `meshSubNumber` | MATCH |
| `hairNumber` | `0x3D4` | float | `hairNumber` | MATCH |
| `dyeNumber` | `0x3D8` | float | `dyeNumber` | MATCH |
| `skinType` | `0x3DC` | int | `skinType` | MATCH |
| `mouthFlapPosRange` | `0x3E0` | float | `mouthFlapPosRange` | MATCH |
| `mouthFlapRotRange` | `0x3E4` | float | `mouthFlapRotRange` | MATCH |
| `mouthSidePosRange` | `0x3E8` | float | `mouthSidePosRange` | MATCH |
| `mouthSideFrequency` | `0x3EC` | float | `mouthSideFrequency` | MATCH |
| `ArmMotionWeight` | `0x3F0` | float | `ArmMotionWeight` | MATCH |
| `ArmGravity` | `0x3F4` | float | `ArmGravity` | MATCH |
| `ArmGravityByPitch` | `0x3F8` | AnimationCurve | `ArmGravityByPitch` | MATCH |
| `ArmStiffness` | `0x400` | float | `ArmStiffness` | MATCH |
| `ArmDamping` | `0x404` | float | `ArmDamping` | MATCH |
| `ArmMotionSpeedLimit` | `0x408` | float | `ArmMotionSpeedLimit` | MATCH |
| `ArmFlexAngle` | `0x40C` | float | `ArmFlexAngle` | MATCH |
| `ArmFlexByPitch` | `0x410` | AnimationCurve | `ArmFlexByPitch` | MATCH |
| `ArmSpinFadeStart` | `0x418` | float | `ArmSpinFadeStart` | MATCH |
| `ArmSpinFadeEnd` | `0x41C` | float | `ArmSpinFadeEnd` | MATCH |
| `SpineLookUpLimit` | `0x420` | float | `SpineLookUpLimit` | MATCH |
| `SpineTwistClamp` | `0x424` | float | `SpineTwistClamp` | MATCH |
| `SpineHeadLookWeightVertical` | `0x428` | float | `SpineHeadLookWeightVertical` | MATCH |
| `HeadYawLimit` | `0x42C` | float | `HeadYawLimit` | MATCH |
| `SpineLowerFollow` | `0x430` | float | `SpineLowerFollow` | MATCH |
| `SpineFollowSmoothSpeed` | `0x434` | float | `SpineFollowSmoothSpeed` | MATCH |
| `movementSounds` | `0x438` | MovementSounds | `movementSounds` | MATCH |
| `showSash` | `0x440` | bool | `showSash` | MATCH |
| `tempPoseType` | `0x444` | int | `tempPoseType` | MATCH |
| `underwearSkin` | `0x448` | uint | `underwearSkin` | MATCH |
| `position` | `0x488` | Vector3 | `position` | MATCH |
| `animator` | `0x678` | Animator | `animator` | MATCH |
| `modelState` | `0x6D8` | %d5d14770 | `modelState` | MATCH |


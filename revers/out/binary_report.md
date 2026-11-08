# Offsets derived from GameAssembly.dll (build 26140533)

Source of every value: `.rdata` field-offset table or a `[this+disp]`
memory operand in the class' own IL2CPP methods.  No live dump and
no `tools/reference` table is read by this script.

- Il2CppType table: `0xFBABD30`
- Il2CppTypeDefinitionSizes table: `0x110F1B00`

## BasePlayer

- field-offset table: not located
- fields: **24**  table: **0**  code: **24**  missing: **0**

| field | offset | evidence |
|---|---|---|
| `UserIDString` | `0x2F0` | `mov qword ptr [rbx + 0x2f0], rax` in `%2dff86d71092c5b934f2637134d8080796829216` @ `0x3E25D21` |
| `blueprints` | `0x318` | `mov rcx, qword ptr [rbx + 0x318]` in `%2dff86d71092c5b934f2637134d8080796829216` @ `0x3E26257` |
| `lastSentTick` | `0x358` | `mov ecx, dword ptr [rax + 0x358]` in `%a0bb7df78a19e5333f3e1f72a87a06c4b782e40e` @ `0x3E6E00B` |
| `currentTeam` | `0x368` | `mov qword ptr [rbx + 0x368], rax` in `%2dff86d71092c5b934f2637134d8080796829216` @ `0x3E26461` |
| `modelState` | `0x398` | `mov r8, qword ptr [rbx + 0x398]` in `%fee90ce8dc753148ed864b0361f1338df70fd03c` @ `0x3E162C2` |
| `voiceRecorder` | `0x3B8` | `cmp byte ptr [rax + 0x3b8], 0` in `%a15d2fe174cc1df3c887712a6132ecbaec19bf2d` @ `0x3E151B8` |
| `eyes` | `0x3C8` | `mov rdi, qword ptr [rcx + 0x3c8]` in `%5c766996bfbec9ad57dc6b2a858d6455d179402f` @ `0x3E19F76` |
| `GestureViewModel` | `0x438` | `mov rcx, qword ptr [rcx + 0x438]` in `%0a7a517922911f9fd1148113c3a6e13d27be1c52` @ `0x3E17FD9` |
| `input` | `0x440` | `mov rcx, qword ptr [rbx + 0x440]` in `%632846ba6b0060f36ef6a08983805bb6ba537152` @ `0x3E1658C` |
| `metabolism` | `0x4C0` | `mov rcx, qword ptr [rbx + 0x4c0]` in `%2dff86d71092c5b934f2637134d8080796829216` @ `0x3E25F50` |
| `hidden_CapsuleCollider` | `0x530` | `cmp qword ptr [rsi + 0x530], 0` in `%a53d56eefa3ed7b084f5ceb065f82efddba26b74` @ `0x3E2277A` |
| `playerRigidbody` | `0x548` | `mov rdi, qword ptr [rbx + 0x548]` in `%9d7c64d306d65975b571e91edb4d1e4f40c1665d` @ `0x3E15B0B` |
| `movement` | `0x550` | `mov rsi, qword ptr [rdi + 0x550]` in `%a15d2fe174cc1df3c887712a6132ecbaec19bf2d` @ `0x3E14F5D` |
| `clActiveItem` | `0x590` | `movups xmm0, xmmword ptr [rbx + 0x590]` in `%4e1a82878afc4b0bd782bc6957239fd42f0c1a03` @ `0x3E18197` |
| `inventory` | `0x5E0` | `cmp qword ptr [rsi + 0x5e0], 0` in `%fc0efab5c4690d365daecd3cce94a3e0002a2d93` @ `0x3E2049A` |
| `mounted` | `0x5E8` | `lea rcx, [rbx + 0x5e8]` in `%76bd5da42efcf21b5df4a612479dfbd809c2ce5a` @ `0x3E152AA` |
| `fallDamageEffect` | `0x6D0` | `mov r9, qword ptr [r10 + 0x6d0]` in `%1b9b52a204928b5e65cb9a949bdd76dd27af4635` @ `0x3E4191B` |
| `drownEffect` | `0x6D8` | `mov rsi, qword ptr [rax + 0x6d8]` in `%c9b84c6b5b7e57cef2c3661f907a040f09adebe1` @ `0x3EB98E2` |
| `playerFlags` | `0x6E0` | `test byte ptr [rbx + 0x6e0], 0x10` in `%6b5a6d4757e5fe49e698eb27e5c3cf0dbc69da8f` @ `0x3E15828` |
| `_displayName` | `0x6F8` | `mov qword ptr [rbx + 0x6f8], r11` in `%15136de954654baa3a722d479526e0fb0d96c7ed` @ `0x3E23844` |
| `voiceSpeaker` | `0x710` | `mov qword ptr [rdi + 0x710], rax` in `%0fa2e4a751fa076c4e1d688b6368ebbfdb06292a` @ `0x3E7B481` |
| `modifiers` | `0x718` | `cmp byte ptr [rcx + 0x718], 0` in `%a52aa23baf70eedd824dbd501d04972b39542691` @ `0x3E21B52` |
| `userID` | `0x728` | `movups xmm0, xmmword ptr [rcx + 0x728]` in `%a0580847a109a1ab61156361e7aa75069b086f50` @ `0x3E15204` |
| `playerModel` | `0x748` | `mov rdi, qword ptr [rbx + 0x748]` in `%ff2b2169a8b379dd96435d8674f0a9f282f7f47a` @ `0x3E189AE` |

## Projectile

- field-offset table: `0xEC2ED00` (layout anchors 34/34)
- fields: **55**  table: **46**  code: **9**  missing: **0**

| field | offset | evidence |
|---|---|---|
| `initialVelocity` | `0x28` | table `0xEC2ED00`[#2] |
| `drag` | `0x34` | table `0xEC2ED00`[#3] |
| `gravityModifier` | `0x38` | table `0xEC2ED00`[#4] |
| `thickness` | `0x3C` | table `0xEC2ED00`[#5] |
| `changeInitialOrientation` | `0x40` | table `0xEC2ED00`[#6] |
| `initialDistance` | `0x44` | table `0xEC2ED00`[#7] |
| `initialOrientation` | `0x48` | table `0xEC2ED00`[#8] |
| `remainInWorld` | `0x54` | table `0xEC2ED00`[#9] |
| `stickProbability` | `0x58` | table `0xEC2ED00`[#10] |
| `breakProbability` | `0x5C` | table `0xEC2ED00`[#11] |
| `conditionLoss` | `0x60` | table `0xEC2ED00`[#12] |
| `ricochetChance` | `0x64` | table `0xEC2ED00`[#13] |
| `penetrationPower` | `0x68` | table `0xEC2ED00`[#14] |
| `canRefract` | `0x6C` | table `0xEC2ED00`[#15] |
| `penetratesVehicles` | `0x6D` | table `0xEC2ED00`[#16] |
| `waterIntegrityLoss` | `0x70` | table `0xEC2ED00`[#17] |
| `damageProperties` | `0x78` | table `0xEC2ED00`[#18] |
| `damageDistances` | `0x80` | table `0xEC2ED00`[#19] |
| `minMax` | `0x80` | table `0xEC2ED00`[#19] |
| `damageMultipliers` | `0x88` | table `0xEC2ED00`[#20] |
| `damageTypes` | `0x90` | table `0xEC2ED00`[#21] |
| `rendererToScale` | `0x98` | table `0xEC2ED00`[#22] |
| `scaleTrailRenderer` | `0x98` | table `0xEC2ED00`[#22] |
| `firstPersonRenderer` | `0xA0` | table `0xEC2ED00`[#23] |
| `scaleTransform` | `0xA0` | table `0xEC2ED00`[#23] |
| `createDecals` | `0xA8` | table `0xEC2ED00`[#24] |
| `doHitEffects` | `0xA9` | table `0xEC2ED00`[#25] |
| `flybySound` | `0xB0` | table `0xEC2ED00`[#26] |
| `soundDefinition` | `0xB0` | table `0xEC2ED00`[#26] |
| `flybySoundDistance` | `0xB8` | table `0xEC2ED00`[#27] |
| `closeFlybySound` | `0xC0` | table `0xEC2ED00`[#28] |
| `closeFlybyDistance` | `0xC8` | table `0xEC2ED00`[#29] |
| `tumbleSpeed` | `0xCC` | table `0xEC2ED00`[#30] |
| `tumbleAxis` | `0xD0` | table `0xEC2ED00`[#31] |
| `playDefaultHitEffects` | `0xDC` | table `0xEC2ED00`[#32] |
| `clientEffectData` | `0xE0` | table `0xEC2ED00`[#33] |
| `customEffectData` | `0xE0` | table `0xEC2ED00`[#33] |
| `clientEffectPrefab` | `0xE8` | table `0xEC2ED00`[#34] |
| `gameObjectRef` | `0xE8` | table `0xEC2ED00`[#34] |
| `swimScale` | `0xF0` | table `0xEC2ED00`[#35] |
| `swimSpeed` | `0xFC` | table `0xEC2ED00`[#36] |
| `baseProjectile` | `0x110` | table `0xEC2ED00`[#38] |
| `projectile` | `0x118` | table `0xEC2ED00`[#39] |
| `hidden_ccfe34b7cfa107117310af889ea8338a5bf48454` | `0x120` | table `0xEC2ED00`[#40] |
| `maxDistance` | `0x140` | `movss xmm0, dword ptr [rcx + 0x140]` in `%34f23f3a6fcda67234b72e4262e1587198a176b7` @ `0x60E5CA0` |
| `currentVelocity` | `0x164` | `lea rdx, [rcx + 0x164]` in `%5bc6b59dfb0da2fcb550c2f40db240fc6a35d533` @ `0x60E57EA` |
| `currentPosition` | `0x170` | `movss xmm8, dword ptr [rcx + 0x170]` in `%5bc6b59dfb0da2fcb550c2f40db240fc6a35d533` @ `0x60E582A` |
| `traveledDistance` | `0x17C` | `comiss xmm0, dword ptr [rbx + 0x17c]` in `%591e32794de5f90460678fc10b2c93aa1a9b5239` @ `0x60E5E9F` |
| `traveledTime` | `0x180` | `comiss xmm0, dword ptr [rcx + 0x180]` in `%34f23f3a6fcda67234b72e4262e1587198a176b7` @ `0x60E5CBE` |
| `sentPosition` | `0x188` | `movss xmm0, dword ptr [rbx + 0x188]` in `%591e32794de5f90460678fc10b2c93aa1a9b5239` @ `0x60E5E32` |
| `previousPosition` | `0x194` | `movsd qword ptr [rbx + 0x194], xmm0` in `%591e32794de5f90460678fc10b2c93aa1a9b5239` @ `0x60E5F89` |
| `previousVelocity` | `0x1A0` | `movsd qword ptr [rbx + 0x1a0], xmm0` in `%c4b0d33f1f7ab6785be047eca02297dc4b2f3f84` @ `0x60E6206` |
| `previousTraveledTime` | `0x1AC` | `mov dword ptr [rbx + 0x1ac], eax` in `%c4b0d33f1f7ab6785be047eca02297dc4b2f3f84` @ `0x60E6259` |
| `mod` | `0x1E0` | table `0xEC2ED00`[#69] |
| `owner` | `0x1F0` | table `0xEC2ED00`[#72] |

## AttackEntity

- field-offset table: `0xEC4E6D0` (layout anchors 21/21)
- fields: **22**  table: **22**  code: **0**  missing: **0**

| field | offset | evidence |
|---|---|---|
| `deployDelay` | `0x2F0` | table `0xEC4E6D0`[#0] |
| `repeatDelay` | `0x2F4` | table `0xEC4E6D0`[#1] |
| `animationDelay` | `0x2F8` | table `0xEC4E6D0`[#2] |
| `effectiveRange` | `0x2FC` | table `0xEC4E6D0`[#3] |
| `npcDamageScale` | `0x300` | table `0xEC4E6D0`[#4] |
| `attackLengthMin` | `0x304` | table `0xEC4E6D0`[#5] |
| `attackLengthMax` | `0x308` | table `0xEC4E6D0`[#6] |
| `attackSpacing` | `0x30C` | table `0xEC4E6D0`[#7] |
| `aiAimSwayOffset` | `0x310` | table `0xEC4E6D0`[#8] |
| `aiAimCone` | `0x314` | table `0xEC4E6D0`[#9] |
| `aiOnlyInRange` | `0x318` | table `0xEC4E6D0`[#10] |
| `CloseRangeAddition` | `0x31C` | table `0xEC4E6D0`[#11] |
| `MediumRangeAddition` | `0x320` | table `0xEC4E6D0`[#12] |
| `LongRangeAddition` | `0x324` | table `0xEC4E6D0`[#13] |
| `CanUseAtMediumRange` | `0x328` | table `0xEC4E6D0`[#14] |
| `CanUseAtLongRange` | `0x329` | table `0xEC4E6D0`[#15] |
| `reloadSounds` | `0x330` | table `0xEC4E6D0`[#16] |
| `thirdPersonMeleeSound` | `0x338` | table `0xEC4E6D0`[#17] |
| `recoilCompDelayOverride` | `0x340` | table `0xEC4E6D0`[#18] |
| `wantsRecoilComp` | `0x344` | table `0xEC4E6D0`[#19] |
| `showCrosshairOnTutorial` | `0x345` | table `0xEC4E6D0`[#20] |
| `noHeadshots` | `0x346` | table `0xEC4E6D0`[#21] |

## PlayerModel

- field-offset table: not located
- fields: **106**  table: **0**  code: **106**  missing: **0**

| field | offset | evidence |
|---|---|---|
| `Shoulders` | `0x98` | `mov rcx, qword ptr [rdi + 0x98]` in `%a8b028ad1eb008208d2ec721e74046d93300490e` @ `0x522EB14` |
| `AdditionalSpineBones` | `0xA0` | `mov rax, qword ptr [rbx + 0xa0]` in `%aac711322f4322b374a9216239b9ecab90a3cafb` @ `0x5226ADE` |
| `_multiMesh` | `0xB8` | `mov rcx, qword ptr [rax + 0xb8]` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5224E2D` |
| `TurnAimSmoothTime` | `0xD0` | `movss dword ptr [rdi + 0xd0], xmm7` in `%8a05b5ecc68441055360e3c2fabbc45c2722a806` @ `0x523D76B` |
| `TurnHead` | `0xD4` | `mov dword ptr [rdi + 0xd4], 1` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225A99` |
| `TurnChest` | `0xE4` | `cmp dword ptr [rcx + 0xe4], 0` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5224E55` |
| `TurnSpine` | `0xF4` | `cmp byte ptr [rax + 0xf4], 0` in `%7f8c4a527b676b00f321130fede6b58501191739` @ `0x5254C76` |
| `TurnPelvis` | `0x104` | `movss xmm1, dword ptr [rdi + 0x104]` in `%e625967b0349a2329592238519f5156c81ccaee7` @ `0x522FA40` |
| `TurnChestLowerShare` | `0x114` | `mov dword ptr [rbx + 0x114], eax` in `%361cd56f3763919ea7f3ed63256ae36ed5f53d02` @ `0x522B1AF` |
| `TurnSpineLowerShare` | `0x118` | `movss xmm1, dword ptr [rdi + 0x118]` in `%e625967b0349a2329592238519f5156c81ccaee7` @ `0x522FC0F` |
| `TurnHeadLockAngle` | `0x11C` | `movss xmm1, dword ptr [rbx + 0x11c]` in `%478736342afffe30da6980e7f0b1eeed20130c74` @ `0x52316E1` |
| `TurnHeadSmoothTime` | `0x120` | `movss xmm2, dword ptr [rdi + 0x120]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C391` |
| `TurnHeadMaxSpeed` | `0x124` | `movss xmm0, dword ptr [rbx + 0x124]` in `%478736342afffe30da6980e7f0b1eeed20130c74` @ `0x523170B` |
| `TurnHeadAimFadeSpeed` | `0x128` | `mov dword ptr [rbx + 0x128], eax` in `%95ad33324cc8b7221dfaf932e298fe324ccd37e5` @ `0x5235C41` |
| `TurnClips` | `0x130` | `movzx eax, byte ptr [r8 + 0x130]` in `%d801592c36e1adff648936e17797f30f4a928f71` @ `0x52300C8` |
| `TurnSpeedByBacklog` | `0x138` | `mov byte ptr [rdi + 0x138], al` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225D44` |
| `TurnMoveThreshold` | `0x140` | `movsd qword ptr [rdi + 0x140], xmm0` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225CEA` |
| `TurnSuppressProceduralLegs` | `0x144` | `mov byte ptr [rcx + 0x144], dl` in `%cd6f5b4af4357192bb62746ecb3b602240acec9c` @ `0x52306F0` |
| `TurnLegBlendTime` | `0x148` | `movss xmm1, dword ptr [rbx + 0x148]` in `%2b86f703c247efce857480adc51de9bccc370ffd` @ `0x5225597` |
| `TurnPelvisEnabled` | `0x14C` | `movsd qword ptr [rdi + 0x14c], xmm0` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225F8A` |
| `TurnPelvisFootPinWeight` | `0x150` | `maxss xmm0, dword ptr [rax + 0x150]` in `%fb0f17b1ae3a5b8c4a47890df829f788ebddfc1e` @ `0x5255CD1` |
| `TurnArmFadeSpeed` | `0x154` | `mov dword ptr [rdi + 0x154], eax` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225F92` |
| `TurnArmFadeWeight` | `0x158` | `mov byte ptr [rdi + 0x158], al` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225FAD` |
| `collision` | `0x210` | `mov rcx, qword ptr [rdi + 0x210]` in `%9b19d85a0465c73b928837fd2522673af9f28c58` @ `0x522BB5E` |
| `censorshipCube` | `0x218` | `mov rdi, qword ptr [rbx + 0x218]` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5225183` |
| `censorshipCubeBreasts` | `0x220` | `mov rdi, qword ptr [rbx + 0x220]` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5225250` |
| `jawBone` | `0x228` | `mov rbx, qword ptr [rdi + 0x228]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C2A4` |
| `neckBone` | `0x230` | `mov rax, qword ptr [rcx + 0x230]` in `%7aaf82e21423370f4cae25a9a8d01afd881e0b1c` @ `0x524AAE6` |
| `headBone` | `0x238` | `mov rdi, qword ptr [rbx + 0x238]` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5225226` |
| `leftEye` | `0x240` | `mov rcx, qword ptr [rbx + 0x240]` in `%86a87fb8a62260b5a67be40dfb322a567d681548` @ `0x5258C26` |
| `rightEye` | `0x248` | `mov rcx, qword ptr [rbx + 0x248]` in `%86a87fb8a62260b5a67be40dfb322a567d681548` @ `0x5258CBB` |
| `eyeController` | `0x250` | `mov rbx, qword ptr [rdi + 0x250]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C6AE` |
| `blinkController` | `0x258` | `mov rsi, qword ptr [rdi + 0x258]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C782` |
| `SpineBones` | `0x260` | `mov rsi, qword ptr [rbx + 0x260]` in `%aac711322f4322b374a9216239b9ecab90a3cafb` @ `0x5226800` |
| `leftFootBone` | `0x268` | `mov rdx, qword ptr [rbx + 0x268]` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225DEB` |
| `rightFootBone` | `0x270` | `mov rcx, qword ptr [rbx + 0x270]` in `%b38e445a4761c66277c1ffec13aea553b5ead312` @ `0x522CAC5` |
| `leftHandPropBone` | `0x278` | `mov rdx, qword ptr [rbx + 0x278]` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225F26` |
| `rightHandPropBone` | `0x280` | `mov rdx, qword ptr [rsi + 0x280]` in `%69ad98c783a3c86b52ab7eacd9916e36e12b13c8` @ `0x524351D` |
| `rightHandTarget` | `0x288` | `movss xmm6, dword ptr [rbx + 0x288]` in `%4432a59f33cd344282822977fc223ffe6c2325c8` @ `0x5238D63` |
| `leftClavicleBone` | `0x298` | `mov rdi, qword ptr [rbx + 0x298]` in `%e108c3d14dcf7d74bfaefda34c9db56f075388a9` @ `0x52470FF` |
| `isPreview` | `0x2A0` | `cmp dword ptr [rcx + 0x2a0], 1` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5224E34` |
| `leftHandTargetPosition` | `0x2A4` | `movss xmm0, dword ptr [rbx + 0x2a4]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CB1B` |
| `leftHandTargetRotation` | `0x2B0` | `movups xmmword ptr [rcx + 0x2b0], xmm0` in `%f24e473409793b70a1c718988004b0ad58b0e85d` @ `0x5225723` |
| `rightHandTargetPosition` | `0x2C0` | `movsd qword ptr [rsi + 0x2c0], xmm0` in `%e715b3715aaa75712bc8475d875fd23f1c872403` @ `0x522D225` |
| `rightHandTargetRotation` | `0x2CC` | `movups xmmword ptr [rsi + 0x2cc], xmm0` in `%e715b3715aaa75712bc8475d875fd23f1c872403` @ `0x522D238` |
| `leftUlnaTwistBone` | `0x2E0` | `mov rsi, qword ptr [rbx + 0x2e0]` in `%b44112f75a5d060db5fac7ed595810e1e342fd63` @ `0x5230467` |
| `rightUlnaTwistBone` | `0x2E8` | `mov rdx, qword ptr [rbx + 0x2e8]` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225AA3` |
| `leftHandTwistRelaxWeight` | `0x2F0` | `movss xmm2, dword ptr [rbx + 0x2f0]` in `%361cd56f3763919ea7f3ed63256ae36ed5f53d02` @ `0x522B124` |
| `rightHandTwistRelaxWeight` | `0x2F4` | `movss xmm7, dword ptr [rbx + 0x2f4]` in `%361cd56f3763919ea7f3ed63256ae36ed5f53d02` @ `0x522B170` |
| `TwistBones` | `0x2F8` | `call qword ptr [rax + 0x2f8]` in `%5a6c64eec6b17ad384d60b166de8dee2fc0303bb` @ `0x5252DFC` |
| `steeringTargetDegrees` | `0x300` | `movss dword ptr [rbx + 0x300], xmm8` in `%b44112f75a5d060db5fac7ed595810e1e342fd63` @ `0x5230454` |
| `playerBoatSteeringTargetDegrees` | `0x304` | `movss xmm0, dword ptr [rbx + 0x304]` in `%d0622d23ae9880c80dfc4ac634d2a077fd880c0d` @ `0x52320F4` |
| `rightFootTargetPosition` | `0x308` | `movsd qword ptr [rsi + 0x308], xmm0` in `%486bfe7015fae557ffc1279c0ff60239e2ce8cdc` @ `0x5248165` |
| `rightFootTargetRotation` | `0x314` | `lea rdx, [rdi + 0x314]` in `%fbb1f84ec2b74c98996ad5c2af586f698aebb589` @ `0x5235D57` |
| `leftFootTargetPosition` | `0x324` | `movss xmm7, dword ptr [rbx + 0x324]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CD87` |
| `leftFootTargetRotation` | `0x330` | `movups xmm0, xmmword ptr [rdx + 0x330]` in `%1e71e09b42f8bda8c5fd2eea214694a24efa6bc4` @ `0x5235CE0` |
| `legsAnimator` | `0x340` | `mov rdi, qword ptr [rbx + 0x340]` in `%2b86f703c247efce857480adc51de9bccc370ffd` @ `0x52254B5` |
| `upperBodyMask` | `0x348` | `mov rax, qword ptr [rcx + r10*8 + 0x348]` in `%4bd3eefaeedc5bed1fd774367ffd549a3761d681` @ `0x522BAAD` |
| `fullMask` | `0x350` | `mov rsi, qword ptr [rdi + 0x350]` in `%2cd2ac9efb63548e0f0ba3319d70fead674c7856` @ `0x523B1F8` |
| `CinematicAnimationController` | `0x358` | `mov qword ptr [rbx + 0x358], 0` in `%d342dc751e2fa20b98a7bbb3c697f82bd3bb6b7a` @ `0x522CE8D` |
| `DefaultAvatar` | `0x360` | `mov rdx, qword ptr [rbx + 0x360]` in `%f574271c4e729485776e569e42c56e7151541a3d` @ `0x5256E78` |
| `CinematicAvatar` | `0x368` | `cmp edi, dword ptr [rax + 0x368]` in `%76045fbb16ea17e56e9eae789935558284c98741` @ `0x526C5B1` |
| `DefaultHoldType` | `0x370` | `mov rsi, qword ptr [rdi + 0x370]` in `%4fbac7e6807fbead20ca82d4659aee339f3435e2` @ `0x5234DD7` |
| `SleepGesture` | `0x378` | `mov rdi, qword ptr [rbx + 0x378]` in `%45c38936f7ce5037c084ec0687885dc0463d8849` @ `0x5235654` |
| `CrawlToIncapacitatedGesture` | `0x380` | `mov rsi, qword ptr [rbx + 0x380]` in `%ac83f0ceef263360205f17348c9b0c2c697857a6` @ `0x52853C4` |
| `CrawlToIncapacitatedGestureHandcuff` | `0x388` | `cmp dword ptr [rax + 0x388], 1` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C251` |
| `StandToIncapacitatedGesture` | `0x390` | `lea rcx, [rbx + 0x390]` in `%45c38936f7ce5037c084ec0687885dc0463d8849` @ `0x52357B5` |
| `MaleSkin` | `0x3A0` | `mov rcx, qword ptr [rdi + 0x3a0]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C37E` |
| `FemaleSkin` | `0x3A8` | `mov rcx, qword ptr [rdi + 0x3a8]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C375` |
| `MannequinSkin` | `0x3B0` | `mov rcx, qword ptr [rdi + 0x3b0]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C363` |
| `subsurfaceProfile` | `0x3B8` | `mov rdi, qword ptr [rsi + 0x3b8]` in `%aed111aba0ff0bdd0285c6eabaeb5d70928c682e` @ `0x524F09B` |
| `voiceVolume` | `0x3C0` | `movss xmm1, dword ptr [rdi + 0x3c0]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C346` |
| `skinColor` | `0x3C4` | `lea r8, [rcx + 0x3c4]` in `%63de193c938e11b71106e3d50aec29845970a1d0` @ `0x5235CB3` |
| `skinNumber` | `0x3C8` | `mov dword ptr [rbx + 0x3c8], 0x80000000` in `%9ed9caf42b8ce876f09dbf7fad6df6f8e0a1d33d` @ `0x523234E` |
| `meshNumber` | `0x3CC` | `movss xmm1, dword ptr [rbx + 0x3cc]` in `%a8b028ad1eb008208d2ec721e74046d93300490e` @ `0x522E8F1` |
| `meshSubNumber` | `0x3D0` | `movss xmm2, dword ptr [rbx + 0x3d0]` in `%a8b028ad1eb008208d2ec721e74046d93300490e` @ `0x522E8E6` |
| `hairNumber` | `0x3D4` | `mulss xmm0, dword ptr [rbx + 0x3d4]` in `%a8b028ad1eb008208d2ec721e74046d93300490e` @ `0x522E92C` |
| `dyeNumber` | `0x3D8` | `mov dword ptr [rcx + 0x3d8], 0x3f800000` in `%14388a86a77bc00ee72f11dc79eb798b416e9675` @ `0x52306DE` |
| `skinType` | `0x3DC` | `cmp dword ptr [rbx + 0x3dc], 1` in `%b9a6cc17f905c5d1f5340ad7ecafd4f4224a2550` @ `0x5225154` |
| `mouthFlapPosRange` | `0x3E0` | `movss xmm1, dword ptr [rbx + 0x3e0]` in `%5f060f742f49a77872b1059899d739dc4d8a1213` @ `0x524DD76` |
| `mouthFlapRotRange` | `0x3E4` | `movss xmm6, dword ptr [rdi + 0x3e4]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C430` |
| `mouthSidePosRange` | `0x3E8` | `mulss xmm8, dword ptr [rdi + 0x3e8]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C3F3` |
| `mouthSideFrequency` | `0x3EC` | `mulss xmm0, dword ptr [rdi + 0x3ec]` in `%e218f0d50f85634a862a4eb302e240d361acafa6` @ `0x522C3D9` |
| `ArmMotionWeight` | `0x3F0` | `movss dword ptr [rbx + 0x3f0], xmm0` in `%d0622d23ae9880c80dfc4ac634d2a077fd880c0d` @ `0x52318A1` |
| `ArmGravity` | `0x3F4` | `movss xmm6, dword ptr [rbx + 0x3f4]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CD12` |
| `ArmGravityByPitch` | `0x3F8` | `mov rcx, qword ptr [rbx + 0x3f8]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CCF5` |
| `ArmStiffness` | `0x400` | `movss xmm6, dword ptr [rbx + 0x400]` in `%bfbc6d3832a082e8f15568b5ea387f2bd13b714a` @ `0x522E70C` |
| `ArmDamping` | `0x404` | `movss xmm1, dword ptr [rbx + 0x404]` in `%03e0804535f2de8a7f80f2fb98247938bc449ea5` @ `0x525B39D` |
| `ArmMotionSpeedLimit` | `0x408` | `movss xmm1, dword ptr [rbx + 0x408]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CB47` |
| `ArmFlexAngle` | `0x40C` | `mov dword ptr [rbx + 0x40c], edi` in `%9ed9caf42b8ce876f09dbf7fad6df6f8e0a1d33d` @ `0x523236F` |
| `ArmFlexByPitch` | `0x410` | `mov rcx, qword ptr [rbx + 0x410]` in `%3216a2395f8f594e338e428f4eb29d8f48d720ab` @ `0x52EA7D0` |
| `ArmSpinFadeStart` | `0x418` | `movss xmm1, dword ptr [rdx + 0x418]` in `%bfbc6d3832a082e8f15568b5ea387f2bd13b714a` @ `0x522E6CF` |
| `ArmSpinFadeEnd` | `0x41C` | `movss xmm0, dword ptr [rbx + 0x41c]` in `%b8fe65ae8a8a63b88c63e2abf171c7f3173a8ce1` @ `0x523CB77` |
| `SpineLookUpLimit` | `0x420` | `lea r8, [rbx + 0x420]` in `%e2f480589c621e1f53eb07ba5cf54dcac169c266` @ `0x5232A03` |
| `SpineTwistClamp` | `0x424` | `movss xmm2, dword ptr [rdx + 0x424]` in `%bfbc6d3832a082e8f15568b5ea387f2bd13b714a` @ `0x522E6C4` |
| `SpineHeadLookWeightVertical` | `0x428` | `lea rcx, [rsi + 0x428]` in `%049f7dd52c6ee86b77809e840e29670c4f55470a` @ `0x524943F` |
| `HeadYawLimit` | `0x42C` | `movss xmm3, dword ptr [rbx + 0x42c]` in `%4ed667f04b1a683cdc0298d2882c10392b8fdf00` @ `0x5256FBA` |
| `SpineLowerFollow` | `0x430` | `lea r10, [rdi + 0x430]` in `%657ba09720f77663a56db22d8a45fb5a848006be` @ `0x5232E4A` |
| `SpineFollowSmoothSpeed` | `0x434` | `movss xmm1, dword ptr [rbx + 0x434]` in `%1724c768f38eb0c77713618c0c271924e2c3df15` @ `0x524552E` |
| `movementSounds` | `0x438` | `mov rdi, qword ptr [rbx + 0x438]` in `%a0ad5562d9d8954896a95e28b02ff5b327f6071f` @ `0x523B546` |
| `showSash` | `0x440` | `movzx eax, byte ptr [rcx + 0x440]` in `%253a3df102407b299d9a406aeb0f8de153c46bb9` @ `0x523A890` |
| `tempPoseType` | `0x444` | `cmp dword ptr [rdi + 0x444], 1` in `%4fbac7e6807fbead20ca82d4659aee339f3435e2` @ `0x5234EAF` |
| `underwearSkin` | `0x448` | `mov r14d, dword ptr [rsi + 0x448]` in `%e28b4b2f9f0329437216202b1161d4de65ef42b8` @ `0x523EB71` |
| `position` | `0x488` | `movsd xmm0, qword ptr [rbx + 0x488]` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x5225CDA` |
| `animator` | `0x678` | `mov rdi, qword ptr [rbx + 0x678]` in `%0f42117493a01bb646192e67a8517ab4ecb64fac` @ `0x523A336` |
| `modelState` | `0x6D8` | `cmp qword ptr [rbx + 0x6d8], 0` in `%4ac60e94f34e2b1ef6237369d1617c562291c937` @ `0x52258FD` |


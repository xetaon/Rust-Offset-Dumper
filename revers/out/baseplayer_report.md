# BasePlayer reverse - build 26140533

- metadata fields: **185**
- metadata rows bound to an offset: **21**
- unresolved hashed rows: **164**
- requested fields emitted: **24 / 24**

## Requested fields

| field | offset | type | decryptor |
|---|---|---|---|
| `UserIDString` | `0x2F0` | il2cpp_type:61337 | - |
| `blueprints` | `0x318` | PlayerBlueprints | - |
| `lastSentTick` | `0x358` | il2cpp_type:55688 | - |
| `currentTeam` | `0x368` | ulong | - |
| `modelState` | `0x398` | il2cpp_type:55706 | - |
| `voiceRecorder` | `0x3B8` | PlayerVoiceRecorder | - |
| `eyes` | `0x3C8` | il2cpp_type:55688 | `PlayerEyesDecrypt` |
| `GestureViewModel` | `0x438` | il2cpp_type:65187 | - |
| `input` | `0x440` | il2cpp_type:55706 | - |
| `metabolism` | `0x4C0` | PlayerMetabolism | - |
| `hidden_CapsuleCollider` | `0x530` | hidden<CapsuleCollider> | `BasePlayerCapsuleCollider` |
| `playerRigidbody` | `0x548` | Rigidbody | - |
| `movement` | `0x550` | il2cpp_type:55706 | - |
| `clActiveItem` | `0x590` | ? | `ClActiveItemDecrypt` |
| `inventory` | `0x5E0` | il2cpp_type:55688 | `PlayerInventoryDecrypt` |
| `mounted` | `0x5E8` | il2cpp_type:40735 | - |
| `fallDamageEffect` | `0x6D0` | il2cpp_type:49357 | - |
| `drownEffect` | `0x6D8` | il2cpp_type:49357 | - |
| `playerFlags` | `0x6E0` | ? | - |
| `_displayName` | `0x6F8` | il2cpp_type:61321 | - |
| `voiceSpeaker` | `0x710` | PlayerVoiceSpeaker | - |
| `modifiers` | `0x718` | il2cpp_type:55706 | - |
| `userID` | `0x728` | ulong | `UserIDDecrypt` |
| `playerModel` | `0x748` | il2cpp_type:55706 | - |

## Every metadata row bound to an offset

| offset | field | type | hash slot |
|---|---|---|---|
| `0x2F0` | `_displayName` | il2cpp_type:61337 | `%b3b0fd5e7b60` |
| `0x318` | `blueprints` | il2cpp_type:55706 | `%e7b0bd099e18` |
| `0x358` | `lastSentTick` | il2cpp_type:55688 | `%18b1720091f7` |
| `0x398` | `modelState` | il2cpp_type:55706 | `%5fe1c8432ff2` |
| `0x3B8` | `voiceRecorder` | il2cpp_type:55706 | `%21fe50e40089` |
| `0x3C8` | `eyes` | il2cpp_type:55688 | `%11c5d9bd7642` |
| `0x438` | `GestureViewModel` | il2cpp_type:65187 | `%-` |
| `0x440` | `input` | il2cpp_type:55706 | `%3539a8c7496d` |
| `0x4C0` | `metabolism` | il2cpp_type:55706 | `%011566333c36` |
| `0x508` | `_lookingAt` | il2cpp_type:55688 | `%0dcd18f7a440` |
| `0x530` | `hidden_CapsuleCollider` | il2cpp_type:55688 | `%e3729f0057ad` |
| `0x548` | `playerRigidbody` | il2cpp_type:55688 | `%71c0c5c736ed` |
| `0x550` | `movement` | il2cpp_type:55706 | `%3e869d6afeaa` |
| `0x5E0` | `inventory` | il2cpp_type:55688 | `%b75fe8cbbdf0` |
| `0x5E8` | `mounted` | il2cpp_type:40735 | `%f7f4524f85b4` |
| `0x6D0` | `fallDamageEffect` | il2cpp_type:49357 | `%-` |
| `0x6D8` | `drownEffect` | il2cpp_type:49357 | `%-` |
| `0x6F8` | `_displayName` | il2cpp_type:61321 | `%5b1153d5d27f` |
| `0x710` | `voiceSpeaker` | il2cpp_type:55706 | `%4d4b99c55904` |
| `0x718` | `modifiers` | il2cpp_type:55706 | `%b481ed2abbac` |
| `0x748` | `playerModel` | il2cpp_type:55706 | `%0d0146cf6ffb` |

## Unresolved (need a live dump or new evidence)

- ord   0  `%989ccd467ba58207082643dbb34b941c3b83eacb`  type `il2cpp_type:55688`
- ord   1  `%6061b7b9341b35f4834670a7a418c4b488f4dbba`  type `il2cpp_type:55688`
- ord   2  `%cef173d05ce0f6f1063049a94ffbcda4fb17cee2`  type `il2cpp_type:55688`
- ord   4  `%43ae9a520ab70d39646d07dbc3784aaf696fb902`  type `il2cpp_type:55688`
- ord   5  `%d40091d2ffac136b864f8da5b67227fcbb18a865`  type `il2cpp_type:55688`
- ord   6  `%a76d4967c7a1d4b0e1ae79ce1cb779202a44fdd1`  type `il2cpp_type:55688`
- ord   7  `%e0c7c9b9cd3337cf9b44e61d389d155fc97d7357`  type `il2cpp_type:55688`
- ord   9  `%f6aeda10bc879edf54baba4b8132f3bf5dfed131`  type `il2cpp_type:55706`
- ord  10  `%44a32bd108fe7f2a133f1656544a5c200f65b046`  type `il2cpp_type:55688`
- ord  11  `%c176cb7e1085d1ddf5d5403dcc399a9e765eb985`  type `il2cpp_type:55688`
- ord  12  `%928fa74cafd2227faa99d9785e0243f1c62f9eab`  type `il2cpp_type:55688`
- ord  13  `%7600c3c18bdbd8d145a7c8fc018261f4f7142fc8`  type `il2cpp_type:55688`
- ord  14  `%1746ed69facf2c16aa336ade7c3263f09e44507b`  type `il2cpp_type:55688`
- ord  15  `%8e2b5e1421b1c3bc10dbd020dde32dfba9bd2c39`  type `il2cpp_type:55688`
- ord  17  `%8ab35a7e33b9d0394a6ec10edbf8693127e6a9dd`  type `il2cpp_type:44241`
- ord  18  `%6903548801a72d9ad25b55a19e2c9f7a5723e4da`  type `il2cpp_type:44258`
- ord  19  `%f370ad539da18caa22c0bec01cb1642c477b4770`  type `il2cpp_type:44241`
- ord  20  `%432e16857153aeed6552030936ec2f829b8ca338`  type `il2cpp_type:44258`
- ord  21  `%319a37fd7bf8427dac9f1e1ce6ad49a9c7e177c2`  type `il2cpp_type:44258`
- ord  22  `%e665f22067ca7c507d27697b1017773ec468ad46`  type `il2cpp_type:44241`
- ord  23  `%d66df96cdecca226551c41b92a34566d19c9bf76`  type `il2cpp_type:44241`
- ord  25  `%889bf88a4c9dda7aa3f203b8ee2a9f77e0e229bc`  type `il2cpp_type:44258`
- ord  26  `%00afe84d6043aea6c2bc076448bc8738b66f7ea4`  type `il2cpp_type:44258`
- ord  27  `%521ce22251906ab3229e94bac78dfd314cabe601`  type `il2cpp_type:55688`
- ord  28  `%16d7d741826657e2d7c2a7b19dffb829cecbe313`  type `il2cpp_type:55688`
- ord  30  `%71f5fd9c6664b60b3f61ae3d378406cbafc019f2`  type `il2cpp_type:55696`
- ord  32  `%1448b626278c5473d68132e17cd4175500f70981`  type `il2cpp_type:44258`
- ord  33  `%85e6b59c90a2f2507b6a47dc8b0f64702eb47cbb`  type `il2cpp_type:44258`
- ord  34  `%425db9cdfb3f5945926c03b6ec757c466cc2d854`  type `il2cpp_type:44258`
- ord  35  `%a1f05f5de472244a10b0e3255577a7a520b79207`  type `il2cpp_type:44258`
- ord  36  `%a6c4328ada177dacfe62bb28a70ec9b1ca21e62b`  type `il2cpp_type:44258`
- ord  37  `%e5a1f01a67c8ae8ccca5bb00999a82db25d28fd6`  type `il2cpp_type:44241`
- ord  38  `%e3f65445143042342f8562509e621fdad2e2254a`  type `il2cpp_type:44241`
- ord  39  `%cbe4c10df5dc05d3975a69d2753827a9b09183fb`  type `il2cpp_type:55706`
- ord  40  `%be7ad368ddfc1c44fb22e6e33fdb6adb0517bb33`  type `il2cpp_type:55688`
- ord  41  `%4b4ed40d0f55fc096bf7ca64e1084753d26ac8af`  type `il2cpp_type:61319`
- ord  42  `%51b4cb3ee06ae765d1a8addde0d045d37a7e9316`  type `il2cpp_type:55688`
- ord  43  `%3361791ca871e9f3655e4cc54724b3e234de32fe`  type `il2cpp_type:44241`
- ord  44  `%d15f2389326acdcb320b70124b710852a363575e`  type `il2cpp_type:44241`
- ord  45  `%0eb9cbef3a1a1f85cda49750ae5fd2a17320f426`  type `il2cpp_type:44241`
- ord  46  `%8339fd851b3b58610d5ec2174134e19ca81d133a`  type `il2cpp_type:44241`
- ord  47  `%6d12e222b4d359b78631e25f905354e044499203`  type `il2cpp_type:44241`
- ord  48  `%83e5d0624848bf35716172b293024c19253e2ed4`  type `il2cpp_type:44241`
- ord  49  `%3cbaab0d09202944a11623f30987cdb4befdf30c`  type `il2cpp_type:44241`
- ord  50  `%4bca21ca6e15f6ac07c24a2e95d7e30205bc2a5c`  type `il2cpp_type:44241`
- ord  51  `%c98deb6028668c2b74b5907561e4ed4724ee5d14`  type `il2cpp_type:44241`
- ord  52  `%47667b342d60561a1d66843136768bf15bf3172a`  type `il2cpp_type:44241`
- ord  53  `%bb7cd32eb58c730c67fc8ae21f8f845272748c64`  type `il2cpp_type:44241`
- ord  54  `%24c4a4c1fd54afeae725adecd804dcec1da63d69`  type `il2cpp_type:44241`
- ord  57  `%4c264881989c5d20f55300eb421bf831a5e118f0`  type `il2cpp_type:44241`
- ord  58  `%eeb91a9d004273b60517a884f2fae6043519b02a`  type `il2cpp_type:44241`
- ord  59  `%3d991fc6605e687df615012f10bfe174df037989`  type `il2cpp_type:44241`
- ord  60  `%3af8aee2bc6e95c439b93e2a7ae2f3fb871309f2`  type `il2cpp_type:44241`
- ord  61  `%329630b4b6be177b75fe9ceae31432f79fdd46dc`  type `il2cpp_type:44241`
- ord  62  `%570010ceabbe420e0242179fb0d868f51ef286b2`  type `il2cpp_type:44241`
- ord  63  `%2660a6eaed8ce1f4c566661adca7c17e0f686cd6`  type `il2cpp_type:44241`
- ord  64  `%1bacfcd1f26edc5cb04c4a738835d63e72945441`  type `il2cpp_type:44241`
- ord  65  `%b43ced6d21fd2376109ad19442f801bcd9790d2f`  type `il2cpp_type:55688`
- ord  66  `%e81b852e4a9c849148564cb232c36d1fa5a8afa8`  type `il2cpp_type:44241`
- ord  67  `%28c598265d11507939e96521c7c9f1969418db32`  type `il2cpp_type:44241`
- ord  68  `%22c4b45e42bfb4e94f0e56b5ef3389f0be1b1a4d`  type `il2cpp_type:55688`
- ord  69  `%c6a5a277a53ebf8ba9a2a1512a0774c440c9a280`  type `il2cpp_type:44241`
- ord  70  `%228d31dc05521d79f479ddfa97f93312c47300df`  type `il2cpp_type:55688`
- ord  71  `%e8e0394c7ef6b4436f21f4b81e03c19005a86b0c`  type `il2cpp_type:55706`
- ord  72  `%f4c9f247ac4c75913cfa314986346f4f9564e8c9`  type `il2cpp_type:44241`
- ord  73  `%6a61824a930b6b88487cfa60135b7c3e52579767`  type `il2cpp_type:55688`
- ord  75  `%a869aa2019b2308936f3e7fa79258cb1a337b7fe`  type `il2cpp_type:55688`
- ord  76  `%373b9599f1d35582ca0b62d157d2d361e8eeb7ac`  type `il2cpp_type:55688`
- ord  77  `%787ad248316dbb4cf96367a88e5573a531c432e4`  type `il2cpp_type:44241`
- ord  78  `%a1a5db14b923eef7514068858ccad02c95d47ab3`  type `il2cpp_type:44241`
- ord  79  `%743a5326140ff6d481b5e245e54abd909a38ffd8`  type `il2cpp_type:44241`
- ord  80  `%fec54ef1786d9de9c3547ec892c19ddbe24fcee2`  type `il2cpp_type:44241`
- ord  81  `%9df8c358cc806b916f078d1f1927c67daaf49166`  type `il2cpp_type:44241`
- ord  82  `%31cb209ece006099c21a4aaeebb24629a3b514f2`  type `il2cpp_type:55688`
- ord  83  `%b796e1f005ef363c65952be22a6fc89fd4981b90`  type `il2cpp_type:55688`
- ord  85  `%925ceeafea164a04c19efe53e6796874b72d1a60`  type `il2cpp_type:44241`
- ord  86  `%83ff9248d9a298cdb3e5e39e5d16d550e37f09e4`  type `il2cpp_type:44241`
- ord  87  `%daa981b89ef0399ca7153095983254e1be8a7d2d`  type `il2cpp_type:55706`
- ord  88  `%cbfaf3cc42872b9884c48563fbf0efceca17f5df`  type `il2cpp_type:55688`
- ord  89  `%83fb5c832d452e35ea202f6bc09e24ada70ffce0`  type `il2cpp_type:55688`
- ord  91  `%e4073536c18df42a1c8cf242b6ec3badb1b293eb`  type `il2cpp_type:55706`
- ord  92  `%18b537bcbf033f5c9354467dd525321c3fb87026`  type `il2cpp_type:55706`
- ord  95  `%7d340d809b3fb1eaa92c9ff3345302d67068623f`  type `il2cpp_type:44258`
- ord  96  `%847676d96790c346f84110470da00e255871e78a`  type `il2cpp_type:44258`
- ord  97  `%1f6a6f722576bd8a86fd5e6b035cfec54453ee30`  type `il2cpp_type:55692`
- ord  98  `%337288e7d25e332c31fc2226280346b0f6910b6e`  type `il2cpp_type:55688`
- ord  99  `%314fdefc6dce4315928384b17f39b3bbc5a52803`  type `il2cpp_type:44241`
- ord 100  `%eca8eaf9febad01c12cb5749529f3d61e21c71bc`  type `il2cpp_type:44241`
- ord 101  `%6cb60f67ea38daeee35ddf5cf19ed83bab66ca13`  type `il2cpp_type:44241`
- ord 102  `%0779465b7ed7c5ffbd0a9da2766854314b608293`  type `il2cpp_type:44241`
- ord 103  `%3939541b2243532b92fbb837cd0a7877c9860a38`  type `il2cpp_type:44241`
- ord 104  `%d2a7cebbefff2655b9f2493aae017b9fd0f599da`  type `il2cpp_type:44241`
- ord 105  `%efb110d955383164fccf64e35e982009b92a4904`  type `il2cpp_type:55688`
- ord 106  `%e23a4daaee7eb264b8efe93b819feb0ce7944b17`  type `il2cpp_type:55688`
- ord 107  `%f2afc63da407e83aec93f909ead4e48de2b56949`  type `il2cpp_type:44241`
- ord 108  `%695cfcb57c499de228ad701ce2374a505bba4aea`  type `il2cpp_type:55706`
- ord 109  `%a3fd4c0318f715f52e2297ae356dd30baf9fe3f3`  type `il2cpp_type:44241`
- ord 110  `%066be769537396f9727bde92b4b71039c06759e8`  type `il2cpp_type:55688`
- ord 111  `%74887725f8ca45d344177d7fd0da60426150ced2`  type `il2cpp_type:44241`
- ord 112  `%216ed001b6cfdaf78db04eb0619ac7d31644d0b9`  type `il2cpp_type:44241`
- ord 115  `%308075171679ba4339de53dc82d203c0a1f52b48`  type `il2cpp_type:44241`
- ord 116  `%8c015cf4522eea15882be2026065f992c007d51b`  type `il2cpp_type:44241`
- ord 117  `%f6243c5be152e483fab01a16d16f96d162f79e2b`  type `il2cpp_type:44241`
- ord 118  `%11d98bc336e1f5cdfefb35a76d7b4f1c66ef6acb`  type `il2cpp_type:55706`
- ord 119  `%836d8d5348d8a037eb3b6313cf0a1775bec7db21`  type `il2cpp_type:44241`
- ord 120  `%4d1d0da2dee26f15e0b946ea61155b2ad4ee27ed`  type `il2cpp_type:44258`
- ord 121  `%55f3eaab8eabc6a9eb9a9e5eb7ad3e47fb6a062f`  type `il2cpp_type:44241`
- ord 122  `%1ed587ce1efbd7074737756c57c66dd54386748d`  type `il2cpp_type:55688`
- ord 123  `%561485dbbfcc0d779bc7f355464a97de20d251f1`  type `il2cpp_type:44241`
- ord 124  `%c3522cd1c7f9d200f33fa5d74e6a0d11d31c02d4`  type `il2cpp_type:44241`
- ord 125  `%be74df7d71b83f12e82a59ddd09bbcf796b6774e`  type `il2cpp_type:44241`
- ord 126  `%e913d861ccdd430160e7ebd0f5973710c584cad9`  type `il2cpp_type:55688`
- ord 127  `%5cb9739c81b35eeb231b77a232c137677897711c`  type `il2cpp_type:44241`
- ord 128  `%0e64fe35aac0f15a97c69500f1271b4de4589f62`  type `il2cpp_type:44241`
- ord 129  `%231759e2417e4193065acb7a865684112169654a`  type `il2cpp_type:44241`
- ord 130  `%c46b0c1a09bec0974c69b59ee77423a17b64e9b0`  type `il2cpp_type:55688`
- ord 131  `%c64000d7156e552ee12f3a9752aa2c64aab5a8d0`  type `il2cpp_type:44241`
- ord 132  `%8ab55078427658d8ca6f997f8e81d0139f5d9888`  type `il2cpp_type:44241`
- ord 133  `%4607c7e3b0cdaeb9286e22bcee1baf2ac47ea064`  type `il2cpp_type:44258`
- ord 134  `%e44e69fd6ad403cf6992fb7258f01e7c17b255c5`  type `il2cpp_type:44241`
- ord 135  `%8eb228825b934a64245d43c3252a59b53b28f11f`  type `il2cpp_type:44241`
- ord 136  `%5838b86b4199ee40c5b18befb80b43d949cbab40`  type `il2cpp_type:55688`
- ord 137  `%e3af64c0c79a39c567c3dc45ba850d0a93f49091`  type `il2cpp_type:44241`
- ord 138  `%828486a3e69f755632e34dbe0d1ad44d8bbb45e3`  type `il2cpp_type:44241`
- ord 139  `%b9fa9bd073715c61ec5690418ccfdb2ca48b44b1`  type `il2cpp_type:44241`
- ord 140  `%a021ff499c092b0aefb57e38c20d8a4f39cec613`  type `il2cpp_type:44241`
- ord 141  `%7c6e064e4d55a7fc45fe6f2004e6f255e15ece91`  type `il2cpp_type:44241`
- ord 142  `%d766f65bbfbdd616b00d6358ca6a7a728acbb6f8`  type `il2cpp_type:55706`
- ord 143  `%07c406db9f7e69b9dd1f924c717d0369337ef755`  type `il2cpp_type:55706`
- ord 144  `%e4304a817eb08b91e7e753cb60275e9477160570`  type `il2cpp_type:44241`
- ord 145  `%49c504eb4a36131b18ef9f0c38aa17ad75c4a383`  type `il2cpp_type:44241`
- ord 146  `%b5e0ea4d0980b45a1a953d87484fff5a7597e043`  type `il2cpp_type:44241`
- ord 147  `%de7ff694e6e3ce0dd9e421b0d0f7297d1b6a9281`  type `il2cpp_type:44241`
- ord 148  `%879a04e00a7b6439c30089a08f4d784f547b8daf`  type `il2cpp_type:44241`
- ord 151  `%6574c5b91e5aff2c93514c9a5f8e3c65c01031ad`  type `il2cpp_type:44258`
- ord 152  `%c074664e85af616bee0355006bd50171a3ffbc1e`  type `il2cpp_type:55688`
- ord 153  `%28bb10bcebbb8c87ccca4f808ccede0f946bf249`  type `il2cpp_type:55706`
- ord 155  `%984bb3708712b2f368632281c58e040f65ec80d0`  type `il2cpp_type:55688`
- ord 156  `%b27f4ee4b5a27056219a33adf7135f2ae8c8bc9e`  type `il2cpp_type:55688`
- ord 159  `%80d7c893a51daa8ef243fbea659698929587c2d2`  type `il2cpp_type:55692`
- ord 160  `%c73d9ab5740d4931bc7cacaa28ea1eb44b2bf55a`  type `il2cpp_type:44258`
- ord 161  `%c257215efc1e54d913b1e389d10b68adb79c10e3`  type `il2cpp_type:55688`
- ord 162  `%affdc648549d107856f707312bfcd8bd897e4e76`  type `il2cpp_type:44258`
- ord 163  `%096a786755a115689b2c77d5b5dc17d1800f4ef6`  type `il2cpp_type:44258`
- ord 165  `%c86b4737b3c6cb4086696a102602aa21d91e98ae`  type `il2cpp_type:55688`
- ord 166  `%07ee17e5742ee1546590b5f2977fb874dae33577`  type `il2cpp_type:44241`
- ord 167  `%f04711b27f3bca48e6f136cdb1514a9b84c7a89a`  type `il2cpp_type:44241`
- ord 168  `%6b31eb0f3351cb7f953eca32dbd68d45e2928a1a`  type `il2cpp_type:44241`
- ord 169  `%5bea4c7b5158e9be691f8111d0cd6db223d84963`  type `il2cpp_type:44241`
- ord 170  `%2b7bc004518f313749138fcee84b5a23b21d314a`  type `il2cpp_type:44241`
- ord 171  `%1e8f296d9dc5ccca3203c4f92187692998157e2a`  type `il2cpp_type:44241`
- ord 172  `%09399cf23857785a4d6734eec0e11a4ca9fa8011`  type `il2cpp_type:55688`
- ord 173  `%ccc9960b04238ef4e67b5b1cc24a0b480cc609e4`  type `il2cpp_type:55688`
- ord 174  `%9f93328e2a466825e3eeaf9d9a0da9fbb5bc5187`  type `il2cpp_type:44241`
- ord 175  `%9fc5696583da91f85542c3e754c558734846ecec`  type `il2cpp_type:44241`
- ord 176  `%91f0b2f4286f2eb8dc1e45a5d955bb9b28d9e6de`  type `il2cpp_type:44258`
- ord 177  `%e0eece91e8b01d53a491be40f3ba18d498420999`  type `il2cpp_type:44258`
- ord 178  `%e553d3fdfd163e0e422dd86045874c201f22ac2b`  type `il2cpp_type:44258`
- ord 179  `%daabe3eb2d3265281b5215f1db62714420dc66bd`  type `il2cpp_type:44258`
- ord 180  `%483c9fbc44aad1aed20d33e4f8d0d4b74b1c5ba7`  type `il2cpp_type:44258`
- ord 181  `%3a0f4eb48b3a4543a71f84640689f0422bb02c3d`  type `il2cpp_type:44258`
- ord 182  `%489cad53ef9c0aeb5aafd7f9c9cd1dcaa26326ec`  type `il2cpp_type:44258`
- ord 183  `%570cc5aa84f79e9af9a7905b08eee593e1c8009b`  type `il2cpp_type:55688`
- ord 184  `%ff669b2c12ef8325e5cd1eddc5e813588703d32d`  type `il2cpp_type:55688`

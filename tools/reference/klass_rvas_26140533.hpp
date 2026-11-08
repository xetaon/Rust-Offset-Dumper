// Community klass_rvas reference for build 26140533 (name -> TypeInfo RVA).
// Used only as a SEED: the dumper still reads the slot at dump time and accepts
// it only when it is either the live klass pointer or a lazy TypeInfo usage token.
namespace klass_rvas
{
    inline static constexpr std::uintptr_t BaseNetworkable = 0x111F0768;
    inline static constexpr std::uintptr_t BaseEntity = 0x1129D198;
    inline static constexpr std::uintptr_t BaseCombatEntity = 0x1129D170;
    inline static constexpr std::uintptr_t BasePlayer = 0x111FFDF0;
    inline static constexpr std::uintptr_t BaseNpc = 0x111FC768;
    inline static constexpr std::uintptr_t BaseVehicle = 0x1120D288;
    inline static constexpr std::uintptr_t DroppedItemContainer = 0x111C0478;
    inline static constexpr std::uintptr_t OreResourceEntity = 0x11253298;
    inline static constexpr std::uintptr_t CollectibleEntity = 0x11253330;
    inline static constexpr std::uintptr_t BuildingBlock = 0x111A27D0;
    inline static constexpr std::uintptr_t BuildingPrivlidge = 0x111E7600;
    inline static constexpr std::uintptr_t Door = 0x111D3A40;
    inline static constexpr std::uintptr_t WorldItem = 0x111BEDB0;
    inline static constexpr std::uintptr_t Signage = 0x11183B28;
    inline static constexpr std::uintptr_t MainCamera = 0x111C43A0;
    inline static constexpr std::uintptr_t ListComponent_Projectile = 0x11204AF0;
    inline static constexpr std::uintptr_t PlayerEyes = 0x111C00E0;
    inline static constexpr std::uintptr_t PlayerModel = 0x111851B0;
    inline static constexpr std::uintptr_t TOD_Sky = 0x11235250;
    inline static constexpr std::uintptr_t Item = 0x11282E80;
    inline static constexpr std::uintptr_t ConsoleSystem_Command = 0x111AF278;
    inline static constexpr std::uintptr_t PlayerInventory_typenav = 0x111C2C80;
    inline static constexpr std::uintptr_t PlayerInput = 0x1122D2A0;
    inline static constexpr std::uintptr_t HeldEntity = 0x112957D0;
    inline static constexpr std::uintptr_t BaseProjectile = 0x11181BA8;
    inline static constexpr std::uintptr_t BaseViewModel = 0x111F9500;
    inline static constexpr std::uintptr_t AutoTurret = 0x111E5910;
    inline static constexpr std::uintptr_t LocalPlayer = 0x111E9EE0;
    inline static constexpr std::uintptr_t ItemIcon = 0x11236AC0;

    // Additional community klass_rvas for build 26140533 (Vlone Generation.h).
    // The resolver still reads every slot and accepts it only when it really
    // holds the matching klass or a well-formed lazy TypeInfo token.
    inline static constexpr std::uintptr_t GameManager = 0x11181780;
    inline static constexpr std::uintptr_t HitTest = 0x11239578;
    inline static constexpr std::uintptr_t ConVar_Graphics = 0x111F03E0;
    inline static constexpr std::uintptr_t ConVar_Admin = 0x11239810;
    inline static constexpr std::uintptr_t PhysX = 0x11203D68;
    inline static constexpr std::uintptr_t MapInterface = 0x1120D750;
    inline static constexpr std::uintptr_t Climate = 0x111FF738;
    inline static constexpr std::uintptr_t AttackEntity = 0x11270730;
    inline static constexpr std::uintptr_t BaseMelee = 0x111BCC48;
    inline static constexpr std::uintptr_t BaseMountable = 0x111F9050;
    inline static constexpr std::uintptr_t StorageContainer = 0x1124F510;
}

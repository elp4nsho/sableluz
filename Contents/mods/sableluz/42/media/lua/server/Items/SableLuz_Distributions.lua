-- Sable de Luz: loot. Generado por build_sableluz.py.
require "Items/ProceduralDistributions"

local LOOT = {
    { "JewelryGems", "SL.CristalKyber", 0.6 },
    { "PawnShopCases", "SL.CristalKyber", 0.4 },
    { "Antiques", "SL.CristalKyber", 0.3 },
    { "LaboratoryLockers", "SL.CristalKyber", 0.5 },
    { "UniversityStorageScience", "SL.CristalKyber", 0.3 },
    { "ComicStoreCounter", "SL.EmpunaduraSable", 0.4 },
    { "ElectronicStoreMisc", "SL.EmpunaduraSable", 0.2 },
    { "CrateElectronics", "SL.EmpunaduraSable", 0.2 },
    { "ArmyStorageElectronics", "SL.EmpunaduraSable", 0.3 },
    { "LaboratoryLockers", "SL.EmpunaduraSable", 0.4 },
    { "LaboratoryLockers", "SL.SableLuz", 0.05 },
    { "ArmyBunkerLockers", "SL.SableLuz", 0.05 },
    { "ArmyStorageGuns", "SL.SableLuz", 0.03 },
    { "PawnShopCases", "SL.SableLuz", 0.03 },
}

local function addLoot()
    for _, row in ipairs(LOOT) do
        local list = ProceduralDistributions.list[row[1]]
        if list and list.items then
            table.insert(list.items, row[2])
            table.insert(list.items, row[3])
        else
            print("[SableLuz] contenedor de loot no encontrado: " .. tostring(row[1]))
        end
    end
end

Events.OnPreDistributionMerge.Add(addLoot)

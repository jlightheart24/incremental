export type LocationDef = {
  locationId: string;
  worldId: string;
  title: string;
  subtitle: string;
  encounterPool: string;
  backgroundImage: string | null;
};

const DESTINY_ISLANDS_BG_DIR = "assets/backgrounds";
const TRAVERSE_TOWN_BG_DIR = "assets/backgrounds";

const LOCATIONS: Record<string, LocationDef> = {
  destiny_islands_beach: {
    locationId: "destiny_islands_beach",
    worldId: "destiny_islands",
    title: "Destiny Islands",
    subtitle: "Beach",
    encounterPool: "destiny_islands_beach",
    backgroundImage: `${DESTINY_ISLANDS_BG_DIR}/destiny_islands.png`
  },
  destiny_islands_cove: {
    locationId: "destiny_islands_cove",
    worldId: "destiny_islands",
    title: "Destiny Islands",
    subtitle: "Cove",
    encounterPool: "destiny_islands_cove",
    backgroundImage: `${DESTINY_ISLANDS_BG_DIR}/destiny_islands.png`
  },
  traverse_town_first_district: {
    locationId: "traverse_town_first_district",
    worldId: "traverse_town",
    title: "Traverse Town",
    subtitle: "First District",
    encounterPool: "traverse_town_first_district",
    backgroundImage: `${TRAVERSE_TOWN_BG_DIR}/traverse_town.png`
  },
  traverse_town_second_district: {
    locationId: "traverse_town_second_district",
    worldId: "traverse_town",
    title: "Traverse Town",
    subtitle: "Second District",
    encounterPool: "traverse_town_second_district",
    backgroundImage: `${TRAVERSE_TOWN_BG_DIR}/traverse_town.png`
  }
};

export const DEFAULT_LOCATION_ID = "destiny_islands_beach";

export function getLocation(locationId: string): LocationDef {
  const location = LOCATIONS[locationId];
  if (!location) throw new Error(`Unknown location '${locationId}'`);
  return location;
}

export function iterLocations(): LocationDef[] {
  return Object.values(LOCATIONS);
}

export { LOCATIONS };

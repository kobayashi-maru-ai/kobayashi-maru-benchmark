import type {
  LeaderboardEntry,
  OriginRegion,
  ReleaseClass,
} from "@/lib/types";

export const releaseClassOptions: ReadonlyArray<{
  value: ReleaseClass;
  label: string;
}> = [
  { value: "closed_proprietary", label: "Closed proprietary" },
  { value: "open_weights", label: "Open weights" },
  { value: "open_source", label: "Open source" },
];

export const originRegionOptions: ReadonlyArray<{
  value: OriginRegion;
  label: string;
}> = [
  { value: "china", label: "China" },
  { value: "united_states", label: "United States" },
  { value: "europe", label: "Europe" },
  { value: "other", label: "Other regions" },
];

export type TaxonomyFilters = {
  releaseClasses: ReleaseClass[];
  originRegions: OriginRegion[];
};

export function filterEntries(
  entries: LeaderboardEntry[],
  { releaseClasses, originRegions }: TaxonomyFilters,
) {
  return entries.filter((entry) => {
    const releaseMatch = releaseClasses.length === 0
      || releaseClasses.includes(entry.release_class);
    const originMatch = originRegions.length === 0
      || originRegions.includes(entry.origin_region);
    return releaseMatch && originMatch;
  });
}

export function releaseClassLabel(value: ReleaseClass) {
  return releaseClassOptions.find((option) => option.value === value)?.label ?? value;
}

export function originRegionLabel(value: OriginRegion) {
  return originRegionOptions.find((option) => option.value === value)?.label ?? value;
}

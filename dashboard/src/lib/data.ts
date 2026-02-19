import type { SprintsData, HypothesesRegistry } from '@/types/sprint';
import sprintsRaw from '../../../sprints.json';
import hypothesesRaw from '../../../hypotheses.json';

export function getSprints(): SprintsData {
  return sprintsRaw as SprintsData;
}

export function getHypotheses(): HypothesesRegistry {
  return hypothesesRaw as HypothesesRegistry;
}

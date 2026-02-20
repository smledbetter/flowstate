import type { SprintsData, HypothesesRegistry, SessionsData } from '@/types/sprint';
import sprintsRaw from '../../../sprints.json';
import hypothesesRaw from '../../../hypotheses.json';
import sessionsRaw from '../../../sessions.json';

export function getSprints(): SprintsData {
  return sprintsRaw as SprintsData;
}

export function getHypotheses(): HypothesesRegistry {
  return hypothesesRaw as HypothesesRegistry;
}

export function getSessions(): SessionsData {
  return sessionsRaw as SessionsData;
}

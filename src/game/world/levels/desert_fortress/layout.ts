import * as THREE from 'three';
import type { ImpactSurface } from '../../WorldTypes';

import {
  addArch,
  addBox,
  addCrateStack,
  addPlane,
  addTrimBand,
  createDesertWorldKit,
  createSiteMarker,
  type WorldBoxSpec,
} from '../../shared/desertWorldKit';

export interface LevelLayoutResult {
  colliders: THREE.Box3[];
  impactSurfaces: ImpactSurface[];
}

export function createDesertFortressLayout(scene: THREE.Scene): LevelLayoutResult {
  const { world, colliders, impactSurfaces, materials } = createDesertWorldKit(scene, {
    worldName: 'world-desert-fortress',
    backgroundColor: 0xc7ae80,
    fogNear: 80,
    fogFar: 230,
    groundSize: 260,
  });

  buildRoutePaving(world, impactSurfaces, materials.stone, materials.accent);
  buildPerimeter(world, colliders, impactSurfaces, materials.plaster);
  buildSouthApproach(world, colliders, impactSurfaces, materials.plaster, materials.trim);
  buildCentralMasses(world, colliders, impactSurfaces, materials.plaster, materials.trim);
  buildNorthCitadel(world, colliders, impactSurfaces, materials.plaster, materials.trim);
  buildCoverAndLandmarks(world, colliders, impactSurfaces, materials.crate, materials.trim);

  return { colliders, impactSurfaces };
}

function buildRoutePaving(
  world: THREE.Group,
  impactSurfaces: Parameters<typeof addPlane>[1],
  stone: THREE.Material,
  accent: THREE.Material,
): void {
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(30, 148),
    position: new THREE.Vector3(0, 0.03, 28),
    material: stone,
    impactSurfaceType: 'stone',
  });
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(34, 162),
    position: new THREE.Vector3(-74, 0.02, 10),
    material: stone,
    impactSurfaceType: 'stone',
  });
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(34, 162),
    position: new THREE.Vector3(74, 0.02, 10),
    material: stone,
    impactSurfaceType: 'stone',
  });
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(92, 58),
    position: new THREE.Vector3(0, 0.04, 6),
    material: accent,
    impactSurfaceType: 'accent',
  });
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(150, 42),
    position: new THREE.Vector3(0, 0.03, -82),
    material: stone,
    impactSurfaceType: 'stone',
  });
}

function buildPerimeter(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addBox>[2],
  plaster: THREE.Material,
): void {
  const perimeter: WorldBoxSpec[] = [
    {
      size: new THREE.Vector3(8, 16, 236),
      position: new THREE.Vector3(-118, 8, 0),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(8, 16, 236),
      position: new THREE.Vector3(118, 8, 0),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(236, 16, 8),
      position: new THREE.Vector3(0, 8, -118),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(88, 16, 8),
      position: new THREE.Vector3(-74, 8, 118),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(88, 16, 8),
      position: new THREE.Vector3(74, 8, 118),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
  ];

  for (const box of perimeter) {
    addBox(world, colliders, impactSurfaces, box);
  }
}

function buildSouthApproach(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addBox>[2],
  plaster: THREE.Material,
  trim: THREE.Material,
): void {
  const southStructures: WorldBoxSpec[] = [
    {
      size: new THREE.Vector3(50, 14, 54),
      position: new THREE.Vector3(-62, 7, 78),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(50, 14, 54),
      position: new THREE.Vector3(62, 7, 78),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(16, 18, 12),
      position: new THREE.Vector3(-28, 9, 112),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(16, 18, 12),
      position: new THREE.Vector3(28, 9, 112),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(22, 12, 18),
      position: new THREE.Vector3(-86, 6, 28),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(22, 12, 18),
      position: new THREE.Vector3(86, 6, 28),
      material: trim,
      impactSurfaceType: 'trim',
    },
  ];

  for (const box of southStructures) {
    addBox(world, colliders, impactSurfaces, box);
  }

  addArch(world, colliders, impactSurfaces, {
    width: 34,
    height: 14,
    depth: 8,
    pillarWidth: 6,
    position: new THREE.Vector3(0, 7, 88),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 26,
    height: 12,
    depth: 8,
    pillarWidth: 5,
    position: new THREE.Vector3(-74, 7, 54),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 26,
    height: 12,
    depth: 8,
    pillarWidth: 5,
    position: new THREE.Vector3(74, 7, 54),
    material: trim,
  });
}

function buildCentralMasses(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addBox>[2],
  plaster: THREE.Material,
  trim: THREE.Material,
): void {
  const centralStructures: WorldBoxSpec[] = [
    {
      size: new THREE.Vector3(44, 14, 54),
      position: new THREE.Vector3(0, 7, 30),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(28, 14, 64),
      position: new THREE.Vector3(-56, 7, 16),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(28, 14, 64),
      position: new THREE.Vector3(56, 7, 16),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(24, 10, 24),
      position: new THREE.Vector3(0, 5, 2),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(22, 12, 16),
      position: new THREE.Vector3(-30, 6, -30),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(22, 12, 16),
      position: new THREE.Vector3(30, 6, -30),
      material: trim,
      impactSurfaceType: 'trim',
    },
  ];

  for (const box of centralStructures) {
    addBox(world, colliders, impactSurfaces, box);
  }

  addArch(world, colliders, impactSurfaces, {
    width: 28,
    height: 12,
    depth: 8,
    pillarWidth: 5,
    position: new THREE.Vector3(-56, 7, -12),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 28,
    height: 12,
    depth: 8,
    pillarWidth: 5,
    position: new THREE.Vector3(56, 7, -12),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 32,
    height: 12,
    depth: 8,
    pillarWidth: 6,
    position: new THREE.Vector3(0, 7, -20),
    material: trim,
  });
}

function buildNorthCitadel(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addBox>[2],
  plaster: THREE.Material,
  trim: THREE.Material,
): void {
  const citadelStructures: WorldBoxSpec[] = [
    {
      size: new THREE.Vector3(44, 14, 50),
      position: new THREE.Vector3(-56, 7, -52),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(44, 14, 50),
      position: new THREE.Vector3(56, 7, -52),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(64, 14, 28),
      position: new THREE.Vector3(0, 7, -84),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(18, 18, 22),
      position: new THREE.Vector3(-88, 9, -84),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(18, 18, 22),
      position: new THREE.Vector3(88, 9, -84),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(20, 10, 14),
      position: new THREE.Vector3(0, 5, -54),
      material: trim,
      impactSurfaceType: 'trim',
    },
  ];

  for (const box of citadelStructures) {
    addBox(world, colliders, impactSurfaces, box);
  }

  addArch(world, colliders, impactSurfaces, {
    width: 36,
    height: 14,
    depth: 8,
    pillarWidth: 6,
    position: new THREE.Vector3(0, 7, -58),
    material: trim,
  });
}

function buildCoverAndLandmarks(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addCrateStack>[2],
  crate: THREE.Material,
  trim: THREE.Material,
): void {
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-84, 0, 62), crate, true);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(68, 0, 60), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-74, 0, -6), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(60, 0, -10), crate, true);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-14, 0, -48), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(8, 0, -68), crate, true);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-66, 0, -94), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(52, 0, -94), crate, false);

  const centralMarker = createSiteMarker('C', '#7d2318');
  centralMarker.position.set(0, 0.05, 2);
  centralMarker.rotation.x = -Math.PI / 2;
  world.add(centralMarker);

  const northMarker = createSiteMarker('N', '#234f74');
  northMarker.position.set(0, 0.05, -86);
  northMarker.rotation.x = -Math.PI / 2;
  world.add(northMarker);

  addTrimBand(world, new THREE.Vector3(-62, 14.2, 78), new THREE.Vector3(52, 0.8, 56), trim);
  addTrimBand(world, new THREE.Vector3(62, 14.2, 78), new THREE.Vector3(52, 0.8, 56), trim);
  addTrimBand(world, new THREE.Vector3(0, 14.2, 30), new THREE.Vector3(46, 0.8, 56), trim);
  addTrimBand(world, new THREE.Vector3(-56, 14.2, -52), new THREE.Vector3(46, 0.8, 52), trim);
  addTrimBand(world, new THREE.Vector3(56, 14.2, -52), new THREE.Vector3(46, 0.8, 52), trim);
  addTrimBand(world, new THREE.Vector3(0, 14.2, -84), new THREE.Vector3(68, 0.8, 30), trim);
}

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

export function createDust2ClassicLayout(scene: THREE.Scene): LevelLayoutResult {
  const { world, colliders, impactSurfaces, materials } = createDesertWorldKit(scene, {
    worldName: 'world-dust2-classic',
    backgroundColor: 0xceb781,
    fogNear: 90,
    fogFar: 240,
    groundSize: 220,
  });

  buildLaneStrips(world, impactSurfaces, materials.stone);
  buildStructuralShell(world, colliders, impactSurfaces, materials.plaster, materials.trim);
  buildArches(world, colliders, impactSurfaces, materials.trim);
  buildCover(world, colliders, impactSurfaces, materials.crate);
  buildLandmarks(world, materials.trim);

  return { colliders, impactSurfaces };
}

function buildLaneStrips(
  world: THREE.Group,
  impactSurfaces: Parameters<typeof addPlane>[1],
  stone: THREE.Material,
): void {
  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(36, 180),
    position: new THREE.Vector3(-73, 0.02, 0),
    material: stone,
    impactSurfaceType: 'stone',
  });

  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(34, 180),
    position: new THREE.Vector3(0, 0.03, 0),
    material: stone,
    impactSurfaceType: 'stone',
  });

  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(36, 180),
    position: new THREE.Vector3(73, 0.02, 0),
    material: stone,
    impactSurfaceType: 'stone',
  });
}

function buildStructuralShell(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addBox>[2],
  plaster: THREE.Material,
  trim: THREE.Material,
): void {
  const structuralBoxes: WorldBoxSpec[] = [
    {
      size: new THREE.Vector3(8, 14, 192),
      position: new THREE.Vector3(-96, 7, 0),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(8, 14, 192),
      position: new THREE.Vector3(96, 7, 0),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(192, 14, 8),
      position: new THREE.Vector3(0, 7, -96),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(192, 14, 8),
      position: new THREE.Vector3(0, 7, 96),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(30, 14, 64),
      position: new THREE.Vector3(-35, 7, 22),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(30, 14, 64),
      position: new THREE.Vector3(35, 7, 22),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(30, 14, 44),
      position: new THREE.Vector3(-35, 7, -58),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(30, 14, 44),
      position: new THREE.Vector3(35, 7, -58),
      material: plaster,
      impactSurfaceType: 'plaster',
    },
    {
      size: new THREE.Vector3(18, 9, 18),
      position: new THREE.Vector3(0, 4.5, -72),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(14, 14, 8),
      position: new THREE.Vector3(-82, 7, -84),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(14, 14, 8),
      position: new THREE.Vector3(82, 7, -84),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(8, 18, 8),
      position: new THREE.Vector3(-88, 9, 88),
      material: trim,
      impactSurfaceType: 'trim',
    },
    {
      size: new THREE.Vector3(8, 18, 8),
      position: new THREE.Vector3(88, 9, 88),
      material: trim,
      impactSurfaceType: 'trim',
    },
  ];

  for (const box of structuralBoxes) {
    addBox(world, colliders, impactSurfaces, box);
  }
}

function buildArches(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addArch>[2],
  trim: THREE.Material,
): void {
  addArch(world, colliders, impactSurfaces, {
    width: 30,
    height: 14,
    depth: 7,
    pillarWidth: 5,
    position: new THREE.Vector3(-73, 7, 10),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 24,
    height: 12,
    depth: 7,
    pillarWidth: 5,
    position: new THREE.Vector3(0, 6, 44),
    material: trim,
  });

  addArch(world, colliders, impactSurfaces, {
    width: 30,
    height: 14,
    depth: 7,
    pillarWidth: 5,
    position: new THREE.Vector3(73, 7, 10),
    material: trim,
  });
}

function buildCover(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: Parameters<typeof addCrateStack>[2],
  crate: THREE.Material,
): void {
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-75, 0, -66), crate, true);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-60, 0, -80), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(75, 0, -66), crate, true);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(60, 0, -80), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(0, 0, 10), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(-8, 0, -12), crate, false);
  addCrateStack(world, colliders, impactSurfaces, new THREE.Vector3(10, 0, -20), crate, false);
}

function buildLandmarks(world: THREE.Group, trim: THREE.Material): void {
  const siteMarkerA = createSiteMarker('A', '#9c2619');
  siteMarkerA.position.set(-72, 0.05, -68);
  siteMarkerA.rotation.x = -Math.PI / 2;
  world.add(siteMarkerA);

  const siteMarkerB = createSiteMarker('B', '#1f4b77');
  siteMarkerB.position.set(72, 0.05, -68);
  siteMarkerB.rotation.x = -Math.PI / 2;
  world.add(siteMarkerB);

  addTrimBand(world, new THREE.Vector3(-35, 14.2, 22), new THREE.Vector3(32, 0.8, 66), trim);
  addTrimBand(world, new THREE.Vector3(35, 14.2, 22), new THREE.Vector3(32, 0.8, 66), trim);
  addTrimBand(world, new THREE.Vector3(-35, 14.2, -58), new THREE.Vector3(32, 0.8, 46), trim);
  addTrimBand(world, new THREE.Vector3(35, 14.2, -58), new THREE.Vector3(32, 0.8, 46), trim);
}

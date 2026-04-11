import * as THREE from 'three';
import type { ImpactSurface, ImpactSurfaceType } from '../WorldTypes';

export interface DesertMaterials {
  plaster: THREE.MeshStandardMaterial;
  trim: THREE.MeshStandardMaterial;
  ground: THREE.MeshStandardMaterial;
  stone: THREE.MeshStandardMaterial;
  crate: THREE.MeshStandardMaterial;
  accent: THREE.MeshStandardMaterial;
}

export interface DesertWorldKit {
  world: THREE.Group;
  colliders: THREE.Box3[];
  impactSurfaces: ImpactSurface[];
  materials: DesertMaterials;
}

export interface WorldBoxSpec {
  size: THREE.Vector3;
  position: THREE.Vector3;
  material: THREE.Material;
  castShadow?: boolean;
  solid?: boolean;
  impactSurfaceType?: ImpactSurfaceType | false;
}

export interface WorldArchSpec {
  width: number;
  height: number;
  depth: number;
  pillarWidth: number;
  position: THREE.Vector3;
  material: THREE.Material;
  impactSurfaceType?: ImpactSurfaceType | false;
}

export interface WorldPlaneSpec {
  size: THREE.Vector2;
  position: THREE.Vector3;
  material: THREE.Material;
  rotationX?: number;
  impactSurfaceType?: ImpactSurfaceType | false;
}

export interface DesertWorldOptions {
  worldName: string;
  backgroundColor?: number;
  fogNear?: number;
  fogFar?: number;
  groundSize?: number;
}

export function createDesertWorldKit(
  scene: THREE.Scene,
  options: DesertWorldOptions,
): DesertWorldKit {
  const backgroundColor = options.backgroundColor ?? 0xceb781;
  const fogNear = options.fogNear ?? 90;
  const fogFar = options.fogFar ?? 240;
  const groundSize = options.groundSize ?? 260;
  const colliders: THREE.Box3[] = [];
  const impactSurfaces: ImpactSurface[] = [];
  const world = new THREE.Group();
  const materials = createDesertMaterials();

  scene.background = new THREE.Color(backgroundColor);
  scene.fog = new THREE.Fog(backgroundColor, fogNear, fogFar);

  world.name = options.worldName;
  scene.add(world);

  const hemisphere = new THREE.HemisphereLight(0xf8efdb, 0x8f5e24, 1.7);
  scene.add(hemisphere);

  const sun = new THREE.DirectionalLight(0xfff3d2, 2.1);
  sun.position.set(60, 95, 30);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 0.5;
  sun.shadow.camera.far = 260;
  sun.shadow.camera.left = -120;
  sun.shadow.camera.right = 120;
  sun.shadow.camera.top = 120;
  sun.shadow.camera.bottom = -120;
  scene.add(sun);

  addPlane(world, impactSurfaces, {
    size: new THREE.Vector2(groundSize, groundSize),
    position: new THREE.Vector3(0, 0, 0),
    material: materials.ground,
    rotationX: -Math.PI / 2,
    impactSurfaceType: 'ground',
  });

  return { world, colliders, impactSurfaces, materials };
}

export function addBox(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: ImpactSurface[],
  spec: WorldBoxSpec,
): void {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(spec.size.x, spec.size.y, spec.size.z),
    spec.material,
  );
  mesh.position.copy(spec.position);
  mesh.castShadow = spec.castShadow ?? true;
  mesh.receiveShadow = true;
  world.add(mesh);

  if (spec.impactSurfaceType !== false) {
    registerImpactSurface(mesh, impactSurfaces, spec.impactSurfaceType ?? 'plaster');
  }

  if (spec.solid ?? true) {
    colliders.push(
      new THREE.Box3().setFromCenterAndSize(spec.position.clone(), spec.size.clone()),
    );
  }
}

export function addPlane(
  world: THREE.Group,
  impactSurfaces: ImpactSurface[],
  spec: WorldPlaneSpec,
): void {
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(spec.size.x, spec.size.y),
    spec.material,
  );
  mesh.position.copy(spec.position);
  mesh.rotation.x = spec.rotationX ?? -Math.PI / 2;
  mesh.receiveShadow = true;
  world.add(mesh);

  if (spec.impactSurfaceType !== false) {
    registerImpactSurface(mesh, impactSurfaces, spec.impactSurfaceType ?? 'ground');
  }
}

export function addArch(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: ImpactSurface[],
  spec: WorldArchSpec,
): void {
  const pillarHeight = spec.height;
  const lintelHeight = 3;
  const openingWidth = spec.width - spec.pillarWidth * 2;

  addBox(world, colliders, impactSurfaces, {
    size: new THREE.Vector3(spec.pillarWidth, pillarHeight, spec.depth),
    position: new THREE.Vector3(
      spec.position.x - openingWidth / 2 - spec.pillarWidth / 2,
      spec.position.y,
      spec.position.z,
    ),
    material: spec.material,
    impactSurfaceType: spec.impactSurfaceType ?? 'trim',
  });

  addBox(world, colliders, impactSurfaces, {
    size: new THREE.Vector3(spec.pillarWidth, pillarHeight, spec.depth),
    position: new THREE.Vector3(
      spec.position.x + openingWidth / 2 + spec.pillarWidth / 2,
      spec.position.y,
      spec.position.z,
    ),
    material: spec.material,
    impactSurfaceType: spec.impactSurfaceType ?? 'trim',
  });

  addBox(world, colliders, impactSurfaces, {
    size: new THREE.Vector3(spec.width, lintelHeight, spec.depth),
    position: new THREE.Vector3(
      spec.position.x,
      spec.position.y + pillarHeight / 2,
      spec.position.z,
    ),
    material: spec.material,
    impactSurfaceType: spec.impactSurfaceType ?? 'trim',
  });
}

export function addCrateStack(
  world: THREE.Group,
  colliders: THREE.Box3[],
  impactSurfaces: ImpactSurface[],
  origin: THREE.Vector3,
  material: THREE.Material,
  doubleHeight: boolean,
): void {
  addBox(world, colliders, impactSurfaces, {
    size: new THREE.Vector3(8, 4, 8),
    position: new THREE.Vector3(origin.x, 2, origin.z),
    material,
    impactSurfaceType: 'crate',
  });

  addBox(world, colliders, impactSurfaces, {
    size: new THREE.Vector3(8, 4, 8),
    position: new THREE.Vector3(origin.x + 8.5, 2, origin.z + 1),
    material,
    impactSurfaceType: 'crate',
  });

  if (doubleHeight) {
    addBox(world, colliders, impactSurfaces, {
      size: new THREE.Vector3(8, 4, 8),
      position: new THREE.Vector3(origin.x + 8.5, 6, origin.z + 1),
      material,
      impactSurfaceType: 'crate',
    });
  }
}

export function addTrimBand(
  world: THREE.Group,
  position: THREE.Vector3,
  size: THREE.Vector3,
  material: THREE.Material,
): void {
  const band = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), material);
  band.position.copy(position);
  band.castShadow = true;
  band.receiveShadow = true;
  world.add(band);
}

export function createSiteMarker(letter: string, color: string): THREE.Mesh {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;

  const context = canvas.getContext('2d');

  if (!context) {
    throw new Error('Unable to create site marker canvas context.');
  }

  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = color;
  context.font = "bold 340px 'Arial Black', sans-serif";
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(letter, 256, 280);

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 8;

  return new THREE.Mesh(
    new THREE.PlaneGeometry(16, 16),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
    }),
  );
}

function createDesertMaterials(): DesertMaterials {
  return {
    plaster: new THREE.MeshStandardMaterial({
      color: 0xd9c398,
      roughness: 0.96,
      metalness: 0.02,
    }),
    trim: new THREE.MeshStandardMaterial({
      color: 0xa98758,
      roughness: 0.9,
      metalness: 0.03,
    }),
    ground: new THREE.MeshStandardMaterial({
      color: 0xc99b5f,
      roughness: 1,
      metalness: 0,
    }),
    stone: new THREE.MeshStandardMaterial({
      color: 0xb78950,
      roughness: 0.95,
      metalness: 0.02,
    }),
    crate: new THREE.MeshStandardMaterial({
      color: 0x7a5731,
      roughness: 0.92,
      metalness: 0.04,
    }),
    accent: new THREE.MeshStandardMaterial({
      color: 0x6f4d29,
      roughness: 0.88,
      metalness: 0.04,
    }),
  };
}

function registerImpactSurface(
  mesh: THREE.Mesh,
  impactSurfaces: ImpactSurface[],
  surfaceType: ImpactSurfaceType,
): void {
  mesh.userData.impactSurfaceType = surfaceType;
  impactSurfaces.push({ mesh, surfaceType });
}

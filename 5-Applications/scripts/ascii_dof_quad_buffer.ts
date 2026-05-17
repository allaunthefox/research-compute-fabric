export type AsciiDofQuadBuffer = {
  buffers: GPUBuffer[];
  cellCount: number;
  byteLength: number;
  currentWrite(frameCounter: number): GPUBuffer;
  currentRead(frameCounter: number): GPUBuffer;
  queued(frameCounter: number): [GPUBuffer, GPUBuffer];
};

declare const GPUBufferUsage: {
  COPY_SRC: GPUBufferUsageFlags;
  COPY_DST: GPUBufferUsageFlags;
  STORAGE: GPUBufferUsageFlags;
  UNIFORM: GPUBufferUsageFlags;
};

export type AsciiDofParams = {
  sourceWidth: number;
  sourceHeight: number;
  gridWidth: number;
  gridHeight: number;
  cellWidth: number;
  cellHeight: number;
  focus: number;
  aperture: number;
  cocScale: number;
  flags?: number;
};

export const ASCII_DOF_PACKED_CELL_BYTES = 4;
export const ASCII_DOF_PARAM_BYTES = 48;
const Q16_SCALE = 65536;

export function toQ16Unit(value: number): number {
  const clamped = Math.min(1, Math.max(0, value));
  return Math.min(0x00010000, Math.round(clamped * Q16_SCALE)) >>> 0;
}

export function createAsciiDofQuadBuffer(
  device: GPUDevice,
  gridWidth: number,
  gridHeight: number,
  label = "ascii-dof",
): AsciiDofQuadBuffer {
  const cellCount = gridWidth * gridHeight;
  const byteLength = cellCount * ASCII_DOF_PACKED_CELL_BYTES;
  const buffers = Array.from({ length: 4 }, (_, i) =>
    device.createBuffer({
      label: `${label}-${i}`,
      size: byteLength,
      usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
    }),
  );

  return {
    buffers,
    cellCount,
    byteLength,
    currentWrite(frameCounter: number) {
      return buffers[frameCounter & 3];
    },
    currentRead(frameCounter: number) {
      return buffers[(frameCounter + 3) & 3];
    },
    queued(frameCounter: number) {
      return [buffers[(frameCounter + 2) & 3], buffers[(frameCounter + 1) & 3]];
    },
  };
}

export function createAsciiDofParamBuffer(device: GPUDevice, label = "ascii-dof-params"): GPUBuffer {
  return device.createBuffer({
    label,
    size: ASCII_DOF_PARAM_BYTES,
    usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
  });
}

export function writeAsciiDofParams(
  device: GPUDevice,
  buffer: GPUBuffer,
  params: AsciiDofParams,
): void {
  const words = new Uint32Array(12);
  words[0] = params.sourceWidth >>> 0;
  words[1] = params.sourceHeight >>> 0;
  words[2] = params.gridWidth >>> 0;
  words[3] = params.gridHeight >>> 0;
  words[4] = params.cellWidth >>> 0;
  words[5] = params.cellHeight >>> 0;
  words[6] = toQ16Unit(params.focus);
  words[7] = toQ16Unit(params.aperture);
  words[8] = toQ16Unit(params.cocScale);
  words[9] = (params.flags ?? 0) & 0xf;
  device.queue.writeBuffer(buffer, 0, words);
}

export function createAsciiDofBindGroup(
  device: GPUDevice,
  layout: GPUBindGroupLayout,
  asciiBuffer: GPUBuffer,
  depthView: GPUTextureView,
  colorView: GPUTextureView,
  paramBuffer: GPUBuffer,
): GPUBindGroup {
  return device.createBindGroup({
    layout,
    entries: [
      { binding: 0, resource: { buffer: asciiBuffer } },
      { binding: 1, resource: depthView },
      { binding: 2, resource: colorView },
      { binding: 3, resource: { buffer: paramBuffer } },
    ],
  });
}

export function decodePackedAsciiCell(packed: number) {
  return {
    depth13: (packed >>> 19) & 0x1fff,
    luma7: (packed >>> 12) & 0x7f,
    char6: (packed >>> 6) & 0x3f,
    flags4: (packed >>> 2) & 0xf,
    reserved2: packed & 0x3,
  };
}

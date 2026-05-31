import wasmModule from "./wasm_compute_bg.wasm";
import { initSync, VmState } from "./wasm_compute.js";

initSync(wasmModule);

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed. Use POST.", { status: 405 });
    }

    const contentType = request.headers.get("content-type") || "";

    try {
      const vm = new VmState();

      if (contentType.includes("application/json")) {
        const body = await request.json();
        if (body.reset) {
          vm.reset();
        }
        if (Array.isArray(body.steps)) {
          for (const s of body.steps) {
            vm.step(s.op || 0, s.idx || 0, s.val || 0);
          }
        }
        const scalar = vm.derive_scalar();
        return new Response(JSON.stringify({ scalar }), {
          headers: { "content-type": "application/json" }
        });
      } else {
        const buffer = await request.arrayBuffer();
        const view = new DataView(buffer);
        const len = buffer.byteLength;

        for (let offset = 0; offset + 2 < len; offset += 3) {
          const op = view.getUint8(offset);
          const idx = view.getUint8(offset + 1);
          const val = view.getInt8(offset + 2);
          vm.step(op, idx, val);
        }

        const scalar = vm.derive_scalar();
        const responseBuf = new ArrayBuffer(2);
        const responseView = new DataView(responseBuf);
        responseView.setUint16(0, scalar, false);

        return new Response(responseBuf, {
          headers: { "content-type": "application/octet-stream" }
        });
      }
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 400,
        headers: { "content-type": "application/json" }
      });
    }
  }
};

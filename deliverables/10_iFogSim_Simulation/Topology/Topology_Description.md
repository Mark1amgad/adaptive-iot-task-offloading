# Implemented Topology

## Devices and Roles

The Java experiment creates exactly three `InstrumentedFogDevice` instances:

| Device | Role | MIPS | RAM | Uplink bandwidth | Downlink bandwidth | Level |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `local` | originating IoT/local executor | 1,000 | 2,000 | 10,000 | 10,000 | 2 |
| `edge` | intermediate fog/edge executor | 2,800 | 4,000 | 10,000 | 10,000 | 1 |
| `cloud` | cloud executor/root | 44,800 | 40,000 | 100,000 | 100,000 | 0 |

The three application modules are placed one per device: `local_executor`, `edge_executor`, and `cloud_executor`. The result endpoint is attached to the local gateway. The Python service is a separate subprocess used for control messages; it is not one of these simulated devices.

## Links

Parent relationships from the Java source are:

`local -> edge -> cloud`

The local device has configured uplink latency `2.0` ms. The edge device has configured uplink latency `45.0` ms to its cloud parent. The source provides the parent-child bandwidth values shown above. Downlink delay is obtained through iFogSim's child latency map; the experiment does not set a separate explicit downlink latency in this source, so that property is marked as simulator-derived/unspecified here rather than invented.

## Route Traversal

- **Local:** task executes at `local`; accepted trace counted 0 bytes on instrumented parent-child links.
- **Edge:** input traverses local-to-edge uplink (12,000 bytes), result traverses edge-to-local downlink (2,000 bytes): 14,000 counted bytes.
- **Cloud:** input traverses local-to-edge and edge-to-cloud uplinks (12,000 bytes each); result traverses cloud-to-edge and edge-to-local downlinks (2,000 bytes each): 28,000 counted bytes.

The diagram reflects the source topology and documents only values found in the Java implementation. It does not imply that Python is a simulated node.

## Diagram Regeneration

From repository root:

```powershell
& python .\deliverables\10_iFogSim_Simulation\Topology\topology_visualization.py
```

This produces `topology.svg` and, when Pillow is available, `topology.png`. The SVG is the more detailed source-grounded diagram; the PNG is a compact visual companion.
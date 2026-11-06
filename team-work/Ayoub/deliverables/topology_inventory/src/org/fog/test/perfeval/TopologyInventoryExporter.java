package org.fog.test.perfeval;

import java.io.BufferedWriter;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.power.models.PowerModel;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;
import org.fog.application.Application;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.placement.Controller;
import org.fog.placement.ModuleMapping;
import org.fog.placement.ModulePlacementMapping;
import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;
import org.json.simple.JSONObject;

/** Exports runtime properties from the unchanged three-device baseline topology. */
public final class TopologyInventoryExporter {
    private static final String APP_ID = "topology-inventory";
    private static final String LOCAL_MODULE = "local_executor";
    private static final String EDGE_MODULE = "edge_executor";
    private static final String CLOUD_MODULE = "cloud_executor";
    private static final double EDGE_CLOUD_LATENCY_MS = 45.0;
    private static final double LOCAL_EDGE_LATENCY_MS = 2.0;

    private TopologyInventoryExporter() { }

    public static void main(String[] args) throws Exception {
        Path output = args.length == 0 ? Path.of("audit_output/topology-work/runtime") : Path.of(args[0]);
        Files.createDirectories(output);
        Log.disable();
        CloudSim.init(1, Calendar.getInstance(), false);
        List<FogDevice> devices = new ArrayList<FogDevice>();
        FogDevice cloud = createDevice("cloud", 44800, 40000, 100000, 100000, 0, 16 * 103, 16 * 83.25);
        cloud.setParentId(-1);
        FogDevice edge = createDevice("edge", 2800, 4000, 10000, 10000, 1, 107.339, 83.4333);
        edge.setParentId(cloud.getId());
        edge.setUplinkLatency(EDGE_CLOUD_LATENCY_MS);
        FogDevice local = createDevice("local", 1000, 2000, 10000, 10000, 2, 87.53, 82.44);
        local.setParentId(edge.getId());
        local.setUplinkLatency(LOCAL_EDGE_LATENCY_MS);
        devices.add(cloud);
        devices.add(edge);
        devices.add(local);

        Application app = Application.createApplication(APP_ID, 0);
        app.addAppModule(LOCAL_MODULE, 64, 1000, 10000);
        app.addAppModule(EDGE_MODULE, 64, 1000, 10000);
        app.addAppModule(CLOUD_MODULE, 64, 1000, 10000);
        ModuleMapping mapping = ModuleMapping.createModuleMapping();
        mapping.addModuleToDevice(LOCAL_MODULE, "local");
        mapping.addModuleToDevice(EDGE_MODULE, "edge");
        mapping.addModuleToDevice(CLOUD_MODULE, "cloud");
        new Controller("topology-inventory-controller", devices, Collections.emptyList(), Collections.emptyList())
                .submitApplication(app, new ModulePlacementMapping(devices, app, mapping));

        List<Map<String, Object>> deviceRows = new ArrayList<Map<String, Object>>();
        Map<Integer, FogDevice> byId = new LinkedHashMap<Integer, FogDevice>();
        Map<String, String> roles = mapOfStrings("cloud", "cloud_executor", "edge", "edge_executor", "local", "local_executor");
        for (FogDevice device : devices) {
            byId.put(device.getId(), device);
            deviceRows.add(deviceRow(device, roles.get(device.getName()), byId));
        }
        List<Map<String, Object>> linkRows = new ArrayList<Map<String, Object>>();
        for (FogDevice child : devices) {
            if (child.getParentId() < 0) continue;
            FogDevice parent = byId.get(child.getParentId());
            Double effective = parent.getChildToLatencyMap().get(child.getId());
            linkRows.add(linkRow(child, parent, effective));
        }
        Map<String, Object> inventory = new LinkedHashMap<String, Object>();
        inventory.put("schema_version", "topology-inventory-v1");
        inventory.put("source", "runtime objects created by TopologyInventoryExporter using the baseline topology");
        inventory.put("python_control_plane", "external JSONL service; not a simulated FogDevice");
        inventory.put("devices", deviceRows);
        inventory.put("links", linkRows);
        writeJson(output.resolve("TOPOLOGY_INVENTORY.json"), inventory);
        writeCsv(output.resolve("TOPOLOGY_INVENTORY.csv"), deviceRows, linkRows);
        Files.writeString(output.resolve("export_status.txt"), "PASS\ndevices=" + deviceRows.size() + "\nlinks=" + linkRows.size() + "\n", StandardCharsets.UTF_8);
        CloudSim.stopSimulation();
    }

    private static FogDevice createDevice(String name, long mips, int ram, long upBw, long downBw,
            int level, double busyPower, double idlePower) throws Exception {
        List<Pe> pes = new ArrayList<Pe>();
        pes.add(new Pe(0, new PeProvisionerOverbooking(mips)));
        PowerHost host = new PowerHost(FogUtils.generateEntityId(), new RamProvisionerSimple(ram),
                new BwProvisionerOverbooking(10000), 1000000, pes, new StreamOperatorScheduler(pes),
                new FogLinearPowerModel(busyPower, idlePower));
        List<Host> hosts = new ArrayList<Host>();
        hosts.add(host);
        FogDeviceCharacteristics characteristics = new FogDeviceCharacteristics("x86", "Linux", "Xen", host,
                10.0, 3.0, 0.05, 0.001, 0.0);
        FogDevice device = new FogDevice(name, characteristics, new AppModuleAllocationPolicy(hosts),
            new LinkedList<Storage>(), 10, upBw, downBw, 0, 0.0);
        device.setLevel(level);
        return device;
    }

    private static Map<String, Object> deviceRow(FogDevice device, String role, Map<Integer, FogDevice> byId) throws Exception {
        PowerHost host = (PowerHost) device.getHost();
        PowerModel power = host.getPowerModel();
        FogDeviceCharacteristics characteristics = (FogDeviceCharacteristics) invoke(device, "getCharacteristics");
        Map<String, Object> row = new LinkedHashMap<String, Object>();
        row.put("name", device.getName()); row.put("id", device.getId()); row.put("role", role);
        FogDevice parent = byId.get(device.getParentId());
        row.put("parent_id", device.getParentId()); row.put("parent_name", parent == null ? null : parent.getName());
        row.put("level", device.getLevel()); row.put("mips", host.getTotalMips()); row.put("ram", host.getRam());
        row.put("pes", host.getNumberOfPes()); row.put("host_storage", host.getStorage()); row.put("host_bandwidth", host.getBw());
        row.put("uplink_bandwidth", device.getUplinkBandwidth()); row.put("downlink_bandwidth", device.getDownlinkBandwidth());
        row.put("uplink_latency_ms", device.getUplinkLatency()); row.put("busy_power", invoke(power, "getMaxPower"));
        row.put("idle_power", invoke(power, "getStaticPower")); row.put("power_model", power.getClass().getName());
        row.put("scheduler", host.getVmScheduler().getClass().getName()); row.put("architecture", invoke(characteristics, "getArchitecture"));
        row.put("os", invoke(characteristics, "getOs")); row.put("vmm", characteristics.getVmm());
        row.put("module", role); row.put("property_sources", "runtime getter/reflection; configured topology values use baseline exporter source");
        return row;
    }

    private static Map<String, Object> linkRow(FogDevice child, FogDevice parent, Double effective) {
        Map<String, Object> row = new LinkedHashMap<String, Object>();
        row.put("source_device", child.getName()); row.put("source_id", child.getId());
        row.put("destination_device", parent.getName()); row.put("destination_id", parent.getId());
        row.put("direction", "child_to_parent / parent_to_child"); row.put("source_uplink_bandwidth", child.getUplinkBandwidth());
        row.put("destination_downlink_bandwidth", parent.getDownlinkBandwidth()); row.put("effective_latency_ms", effective);
        row.put("latency_source", "derived_by_Controller_from_child_uplink_latency");
        row.put("controller_registered", parent.getChildToLatencyMap().containsKey(child.getId()));
        return row;
    }

    private static Object invoke(Object target, String name) throws Exception {
        Class<?> type = target.getClass();
        while (type != null) {
            try {
                Method method = type.getDeclaredMethod(name);
                method.setAccessible(true);
                return method.invoke(target);
            } catch (NoSuchMethodException missing) {
                type = type.getSuperclass();
            }
        }
        throw new NoSuchMethodException(target.getClass().getName() + "." + name);
    }

    private static void writeJson(Path path, Map<String, Object> data) throws IOException {
        Files.writeString(path, JSONObject.toJSONString(data), StandardCharsets.UTF_8);
    }

    private static void writeCsv(Path path, List<Map<String, Object>> devices, List<Map<String, Object>> links) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            writer.write("record_type,name_or_source,id_or_source,parent_or_destination,role_or_direction,mips,ram,pes,host_storage,host_bandwidth,uplink_bandwidth,downlink_bandwidth,latency_ms,module,latency_source");
            writer.newLine();
            for (Map<String, Object> row : devices) writer.write(csv("device", row.get("name"), row.get("id"), row.get("parent_id"), row.get("role"), row.get("mips"), row.get("ram"), row.get("pes"), row.get("host_storage"), row.get("host_bandwidth"), row.get("uplink_bandwidth"), row.get("downlink_bandwidth"), row.get("uplink_latency_ms"), row.get("module"), "runtime"));
            for (Map<String, Object> row : links) writer.write(csv("link", row.get("source_device"), row.get("source_id"), row.get("destination_device"), row.get("direction"), "", "", "", "", "", row.get("source_uplink_bandwidth"), row.get("destination_downlink_bandwidth"), row.get("effective_latency_ms"), "", row.get("latency_source")));
        }
    }

    private static String csv(Object... values) { return Arrays.stream(values).map(value -> value == null ? "" : String.valueOf(value)).map(value -> "\"" + value.replace("\"", "\"\"") + "\"").reduce((a, b) -> a + "," + b).orElse("") + "\n"; }
    private static Map<String, String> mapOfStrings(String... values) { Map<String, String> map = new LinkedHashMap<String, String>(); for (int i = 0; i < values.length; i += 2) map.put(values[i], values[i + 1]); return map; }
}

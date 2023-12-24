import os
import psutil

if os.name == "posix":
    import pyudev
    from pyudev import Device
else:
    pyudev = None
    Device = None

class DeviceManagerLinux:
    def __init__(self):
        self.devices = []
        self.partitions = []
        self.mountpoints = []
        self.context = pyudev.Context()

    def get_devices(self) -> list[Device]:
        device_list = self.context.list_devices(subsystem="block", DEVTYPE="disk")

        self.devices.extend(d for d in device_list if d.attributes.asstring("removable") == "1")

        return self.devices

    def get_partitions(self) -> list[str]:
        if not self.devices:
            self.get_devices()

        partition_list = self.context.list_devices(subsystem="block", DEVTYPE="partition")

        for device in self.devices:
            self.partitions.extend(d.device_node for d in partition_list if d.parent == device)

        return self.partitions

    def get_mountpoints(self) -> list[str]:
        if not self.partitions:
            self.get_partitions()

        for partition in self.partitions:
            self.mountpoints.extend(p.mountpoint for p in psutil.disk_partitions() if p.device == partition)

        return self.mountpoints

    def watch(self):
        monitor = pyudev.Monitor.from_netlink(self.context)
        monitor.filter_by("block")

        for device in iter(monitor.poll, None):
            # "ID_FS_TYPE" in device (partition not a filesystem)
            if device.device_node[5:7] == "sd":
                disk_partitions = psutil.disk_partitions()

                if device.action == "add":
                    # node is the raw device, not a partition
                    if not device.device_node[-1].isdigit():
                        self.devices.append(device)
                        print("Périphérique ajouté :", device.device_node)
                    else:
                        self.partitions.append(device.device_node)
                        print("Partition ajoutée :", device.device_node)

                    for p in disk_partitions:
                        if p.device == device.device_node:
                            self.mountpoints.append(p.mountpoint)
                            print("Partition montée :", p.mountpoint)
                elif device.action == "remove":
                    # node is the raw device, not a partition
                    if not device.device_node[-1].isdigit():
                        self.devices.remove(device)
                        print("Périphérique retiré :", device.device_node)
                    else:
                        self.partitions.remove(device.device_node)
                        print("Partition retirée :", device.device_node)

                    # check if mountpoint is still mounted
                    for mountpoint in self.mountpoints:
                        if mountpoint not in [p.mountpoint for p in disk_partitions]:
                            self.mountpoints.remove(mountpoint)
                            print("Partition démontée :", mountpoint)

if os.name == "posix":
    DeviceManager = DeviceManagerLinux
else:
    DeviceManager = None



if __name__ == "__main__":
    if not DeviceManager:
        print("Error: DeviceManager is not available on this platform.")
        raise SystemExit

    device_manager = DeviceManager()

    devices = device_manager.get_devices()
    partitions = device_manager.get_partitions()
    mountpoints = device_manager.get_mountpoints()

    print("Périphériques détectés :", ", ".join([f"{device.get('ID_VENDOR')} {device.get('ID_MODEL')} -> {device.device_node}" for device in devices]))

    print("Partitions détectées :", ", ".join(partitions))

    print("Partitions montées :", ", ".join(mountpoints))

    device_manager.watch()

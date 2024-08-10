from command import Command
import struct


def main():
    # Create an instance of Command.Header
    header = Command.Header(type=1, stream_id=123, frame_id=456)

    # Print the attributes to verify they are set correctly
    print(f"Type: {header.type}")
    print(f"Stream ID: {header.stream_id}")
    print(f"Frame ID: {header.frame_id}")

    # Use struct to pack the header data
    packed_data = header.pack()
    print(f"Packed Data: {packed_data}")

    # Unpack the data to verify it matches the original values
    unpacked_data = struct.unpack(Command.Header.format_string, packed_data)
    print(f"Unpacked Data: {unpacked_data}")


if __name__ == "__main__":
    main()

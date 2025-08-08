import argparse
import yaml

from mqi_communicator.container import Container
from mqi_communicator.controllers.application import Application

def main():
    """
    The main entry point for the MQI Communicator application.
    """
    parser = argparse.ArgumentParser(description="MQI Communicator")
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file."
    )
    args = parser.parse_args()

    # Load configuration from YAML file
    try:
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{args.config}'")
        exit(1)
    except Exception as e:
        print(f"Error: Could not read or parse configuration file: {e}")
        exit(1)

    # Initialize the DI container
    container = Container()

    # Provide the configuration to the container
    container.config.from_dict(config_data)

    # The container needs to be wired to instantiate the providers
    # We are not injecting into any modules right now, but this is good practice.
    container.wire(modules=[__name__])

    # Get the application instance from the container
    application = container.application()

    # Run the application
    application.run()

if __name__ == "__main__":
    main()

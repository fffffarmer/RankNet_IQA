import argparse
import collections

import numpy as np
import torch
import torch.nn as nn

import dataset as module_data
import metric as module_metric
import model as module_arch
from parse_config import ConfigParser
from utils.common import prepare_device

def main(config):
    # Setup the dataset.
    print("It may take some time to prepare data (even longer if pin_memory is set).")
    kwargs = config["dataloader"]["args"]
    kwargs["validation_split"] = 0.0
    kwargs["split"] = "test"
    test_dataloader = getattr(module_data, config["dataloader"]["type"])(**kwargs)

    # Build the model architecture, then print it to console.
    model = config.init_obj("arch", module_arch)
    print(model)

    # Load the checkpoint.
    if config.resume:
        print("Loading checkpoint: {}...".format(config.resume))
        checkpoint = torch.load(config.resume)
        state_dict = checkpoint["state_dict"]
        model.load_state_dict(state_dict)

    # Prepare GPU(s).
    device, device_ids = prepare_device(config["n_gpu"])
    model = model.to(device)
    if len(device_ids) > 1:
        model = torch.nn.DataParallel(model, device_ids=device_ids)

    # Set the eval mode.
    model.eval()

    with torch.no_grad():
        for _, ((first_data_batch, second_data_batch), label_batch) in enumerate(test_dataloader):
            # Forward.
            first_data_batch, second_data_batch, label_batch = first_data_batch.to(device), second_data_batch.to(device), label_batch.to(device)
            outputs = model(first_data_batch, second_data_batch)
            outputs, label_batch = outputs.cpu().numpy()[:, 0], label_batch.cpu().numpy()[:, 0]
            acc = module_metric.accuracy(outputs, label_batch)

            print(acc)

if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Test.")
    args.add_argument("-c", "--config", default=None, type=str, help="config file path (default: None)")
    args.add_argument("-r", "--resume", default=None, type=str, help="path to latest checkpoint (default: None)")
    args.add_argument("-d", "--device", default=None, type=str, help="indices of GPUs to enable (default: all)")

    config = ConfigParser.from_args(args, enable_log=False)

    # Let"s get started.
    main(config)

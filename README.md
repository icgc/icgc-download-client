# ICGC Download Client
Universal download client for ICGC data residing in various environments. 

## Installing the Python Script

The python script can be installed by simply navigating to the `icgc-download-client` directory and running the command:

```shell
python setup.py install
```

## Using the Python Script

The required arguments for the python script are the repository that is being targeted for download.
Valid repositories are:

* `aws` _(Amazon Web Services)_
* `collab` _(Collabratory)_
* `ega` _(European Genome Association)_
* `gdc` _(Genomic data commons)_
* `cghub` _(Cancer genomic hub)_

Second you must specify either a file id using the tag `-f` or `--file`, a manifest file using the tags `-m` or `--manifest`
or both.  This will specify the file or files to be downloaded.  **The EGA repository does not currently support
downloads using a manifest file.**  It is possible to specify multiple file ID's using the `-f` flag when downloading from the
gdc or cghub repositories.  **The EGA and ICGC repositories do not support this functionality**

If not running the tool in a docker container, a user must also specify the `--output` where files are to be saved
and the `--config`, the location of the configuration file.  **Absolute paths are required for both arguments.**

## Using the Docker Container

To save some typing, you can add a convenience bash alias to make working with the container easier:

```shell
alias icgc-download-client="docker run -it --rm -v {PATH}/icgc-download-client/mnt:/icgc/mnt icgc"
```

replacing `{PATH}` with the path to your mounted directory.  This directory must contain three subdirectories:
 * an empty`downloads` directory.
 * a `conf` directory containing the config.yaml file.
 * an empty logs directory`logs`.

This will enable the invocation of the python script with the command `icgc-download-client`.  When running through the docker container there is no
 need to use the `--output` or `--config` arguments.

Then execute the command as normal:

```shell
icgc-download-client collab -f  FI378424
```

Sample commands (require valid icgc and ega credentials)

icgc-download-client cghub -f a337c425-4314-40c6-a40a-a444781bd1b7

icgc-download-client ega  -f EGAD00001001847

icgc-download-client collab -f a5a6d87b-e599-528b-aea0-73f5084205d5

icgc-download-client gdc -f f483ad78-b092-4d10-9afb-eccacec9d9dc

icgc-download-client collab 9c18cbb9-aaa8-4157-b2dc-a857b1096a6a

icgc-download-client gdc -f 2c759eb8-7ee0-43f5-a008-de4317ab8c70 a6b2f1ff-5c71-493c-b65d-e344ed29b7bb

icgc-download-client cghub  -f a452b625-74f6-40b5-90f8-7fe6f32b89bd a105a6ec-7cc3-4c3b-a99f-af29de8a7caa







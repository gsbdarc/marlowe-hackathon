# Settings for the beginner track on the Yens. Source it from the top of the repo, don't run it:
#   source scripts/beginner/yens.sh
# It is env/yens.sh unchanged: the beginner track reads the shared, read-only data the instructors prepared
# ($CLASS_DATA), so there is no copy of Jev's release to make and nothing to point $DATA at.
source env/yens.sh
mkdir -p logs                                                # Slurm writes each job's log here, and will not make the folder

# Shared settings for the Globus scripts. Source, don't run.
GLOBUS=${GLOBUS:-/scratch/users/$USER/globus-venv/bin/globus}
YEN=2556f515-7a87-407b-a24d-18ed16237588       # "GSB/DARC yen" mapped collection; full /zfs paths
MARLOWE=56ac92ca-0bad-4009-baaa-513525b3e648   # "Marlowe /scratch directories"
# The Marlowe collection root is /scratch, so /scratch/m000106/... is /m000106/... in Globus.
MARLOWE_ROOT=/m000106/gsb_hackathon/cyber-distill
YEN_ROOT=/zfs/projects/darc/marlowe_hackathon/cyber-distill

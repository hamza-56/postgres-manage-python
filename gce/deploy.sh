MY_INSTANCE_NAME="campaign-planner"
ZONE=us-central1-a

gcloud compute instances create $MY_INSTANCE_NAME \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --machine-type=e2-micro \
    --scopes userinfo-email,cloud-platform \
    --metadata-from-file startup-script=startup-script.sh \
    --zone $ZONE \
    --tags http-server

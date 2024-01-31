FIXME: automated testing for lib/tf_lock

```console
cd slice-0-project
alias sudo-plan='sudo-gcp -u tacos-gha-tf-plan@sac-dev-sa.iam.gserviceaccount.com'
alias sudo-apply='sudo-gcp -u tacos-gha-tf-apply@sac-dev-sa.iam.gserviceaccount.com'

sudo-plan tf-lock-info
> {"lock": false}

sudo-apply tf-lock-info
> {"lock": false}

sudo-plan tf-lock-acquire
> ╷
> │ Error: Error acquiring the state lock
> │
> │ Error message: 2 errors occurred:
> │       * writing "gs://mybucket/slice-0-project/default.tflock" failed: googleapi: Error 403:
> │ tacos-gha-tf-plan@sac-dev-sa.iam.gserviceaccount.com does not have storage.objects.create access to the Google Cloud Storage object.
> │ Permission 'storage.objects.create' denied on resource (or it may not exist)., forbidden
> │       * storage: object doesn't exist
> │
> │
> │
> │ Terraform acquires a state lock to protect the state from being written
> │ by multiple users at the same time. Please resolve the issue above and try
> │ again. For most commands, you can disable locking with the "-lock=false"
> │ flag, but this is not recommended.
> ╵
> lock not obtained!
> exit code: 1


sudo-apply tf-lock-acquire
> 1111111111111111

# acquiring an already-acquired lock succeeds:
sudo-apply tf-lock-acquire
> 1111111111111111

# ... even when readonly
sudo-plan tf-lock-acquire
> 1111111111111111

sudo-plan tf-lock-info
> {"ID": "1111111111111111","Path": "gs://mybucket/slice-0-project/default.tflock","Operation": "OperationTypeInvalid","Who": "buck@localhost.lan","Version": "1.6.4","Created": "2023-12-22 22:27:44.186639 +0000 UTC","Info": "","lock":true}

sudo-apply tf-lock-info
> {"ID": "1111111111111111","Path": "gs://mybucket/slice-0-project/default.tflock","Operation": "OperationTypeInvalid","Who": "buck@localhost.lan","Version": "1.6.4","Created": "2023-12-22 22:27:44.186639 +0000 UTC","Info": "","lock":true}

sudo-plan tf-lock-release
> Failed to unlock state: googleapi: Error 403: tacos-gha-tf-plan@sac-dev-sa.iam.gserviceaccount.com does not have storage.objects.delete access to the Google Cloud Storage object. Permission 'storage.objects.delete' denied on resource (or it may not exist)., forbidden
> Lock Info:
>   ID:        1111111111111111
>   Path:      gs://mybucket/slice-0-project/default.tflock
>   Operation: OperationTypeInvalid
>   Who:       buck@localhost.lan
>   Version:   1.6.4
>   Created:   2023-12-22 22:27:44.186639 +0000 UTC
>   Info:
>
> exit code: 1

sudo-apply tf-lock-release
> Terraform state has been successfully unlocked!
>
> The state has been unlocked, and Terraform commands should now be able to
> obtain a new lock on the remote state.

# releasing an already-released lock is successful
sudo-plan tf-lock-release
> (terraform state not locked)

# ... even when readonly
sudo-apply tf-lock-release
> (terraform state not locked)
```

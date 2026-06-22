# Clear out the old tag checkpoint locally and remotely
git tag -d v0.1.8
git push origin --delete v0.1.8

# Re-attach the tag cleanly to your fixed main commit
git tag -a v0.1.10 -m "Release v0.1.10"
git push origin v0.1.10
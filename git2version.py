import git   # Needs gitpython installing
import os


def gitversion(repopath=None, verbose=True, errorstop=True, branchname=True, ignorechanges=False):
    if not repopath:
        repopath = "."
    repofullpath = os.path.abspath(repopath)
    if verbose:
        print('GITVERSION')
        print('==========')
        print(f"Checking git repo[{repofullpath}] for tag of major#.minor#.fix#")
    repo = git.Repo(repopath)

    errors = []
    if repo.is_dirty():
        errors.append(
            f"ERROR: Repo({repofullpath}) has outstanding changes (commit needed)"
        )
    if len(repo.tags) < 1:
        errors.append(
            f'ERROR: Commits untagged - add version tag using: git tag -a major#.minor#.fix# -m "message"'
        )

    tagdict = {i.commit: i for i in repo.tags}
    # print(tagdict)

    commit = None
    for i, commit in enumerate(repo.iter_commits()):
        if commit in tagdict:
            break

    lasttag = "0.0.0"
    commitcount = 0
    if commit in tagdict:
        lasttag = tagdict[commit]
        commitcount = i
    versplit = str(lasttag).split(".")

    if (
        len(versplit) != 3
        or not versplit[0].isnumeric()
        or not versplit[1].isnumeric()
        or not versplit[2].isnumeric()
    ):
        errors.append(
            f"ERROR: Invalid version format: {lasttag} (expected: major#.minor#.fix#)"
        )

    # Add branch name if not on main/master branch:
    if branchname and repo.active_branch.name.lower() not in ('main', 'master'):
        lasttag = f'{repo.active_branch.name}-{lasttag}'
        if verbose:
            print(f'Not on main/master branch so prefixing branch name: {repo.active_branch.name}')

    if errors:
        for i in errors:
            print(i)
        if errorstop:
            print('ERROR: Git version validation failure.  Check with "git status"')
            exit(1)
        elif not ignorechanges:
            if verbose: print(f'WARNING: Adding verification failure tag: {lasttag}-VF-{commitcount}')
            return f"{lasttag}-VF-{commitcount}"  # Add in a Verification Failure prefix

    if verbose:
        if commitcount > 0:
            print(f"WARNING: commit revisions since last tag are {commitcount}.")
            print(f"You may want to update current version {lasttag} with:")
            print("    git tag -a major#.minor#.fix# -m <message>")
        print(f"Version is {lasttag}-{commitcount}")

    return f"{lasttag}-{commitcount}"



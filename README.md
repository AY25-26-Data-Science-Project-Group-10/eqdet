# Training an ML-algorithm for real-time earthquake detection in Finland

University of Helsinki course: Data Science Project

Developers: Teemu Ruokokoski, Tom Cordruwisch, De Qi Ng, Ceren Sahin, Tuula Salmi

# Git Workflow


## Important Rules
* Everyone commits **directly to `main`** (the main branch)
* If you push code to `main`, **you** are responsible for making sure it **does not break the project**.

## How to make commits
### 1. Get the latest code 
Before you start working, always get the latest code first:
```
git pull
```

### 2. Check which files you have changed
After you make changes, check which files you changed:
```
git status
```

### 3. Add your changes
Tell Git which are the files you plan to commit using `git add`: 

To add all files:
```
git add .
```

To add one file:
```
git add filename.ext
```

### 4. Commit your changes 
Committing means to capture a snapshot of the files at their current state. Do give a short but informative summary about the changes. 
```
git commit -m "Describe what you changed"
```
Example:
```
git commit -m "Fix login bug"
```

### 5. Push to `main`
```
git push origin
```
The code can now be seen on Github!


## What if multiple people are editing the same file?

Ideally, our job scopes are independent of each other and we work on different files. But that is not always possible, creating a situation where:
1. You made new local (copy on your laptop) changes to a file in an older commit you pulled from Github
2. And someone else pushed a new commit to Github which changed the same file

Here is how to update your local (your laptop) repository with the latest commits from Github without erasing your (uncommitted) work. 

### 1. Git stash your changes
Use `git stash` to temporarily shelve the changes you've made to your local copy.
```
git stash
```

### 2. Pull the latest commits from github
```
git pull origin
```

### 3. Reapply your stashed changes
Apply the latest stashed element from the stash stack on your local repository:
```
git stash pop
```

### 4. Resolve bugs and continue your work
Since your code is mixed in with new code, there might be bugs. Resolve them and continue with your work :)
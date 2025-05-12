#!/bin/bash

edit_changelog() {
    echo "Editting changelog"
    LASTHEAD=$(grep HEAD CHANGELOG.md)
    LASTV=$(echo $LASTHEAD | grep -Po "compare/\K(v[0-9]\.[0-9]*\.[0-9]*)")

    sed -i "s/$LASTV\.\./v$VERSAO\.\./" CHANGELOG.md
    sed -i "/^\[unreleased/a [${VERSAO/v/}]: https://github.com/leafarlins/$SITENAME/compare/$LASTV..$VERSAO/" CHANGELOG.md
    sed -i "/^## \[unreleased/a ## \[$VERSAO\] - $HOJE" CHANGELOG.md
    #sed -n '/## \[unreleased/,/^## /p' CHANGELOG.md | sed '/^## \[/d' > /tmp/tagnotes

    sed -i "s;leafarlins/$SITENAME v.*;leafarlins/$SITENAME v$VERSAO/" app/templates/about.html
}

commit_tag() {
    echo "Committing"
    git add CHANGELOG.md
    git add app/templates/about.html
    git commit -m "release v$VERSAO"
    git tag v$VERSAO
    git push --tags
    #git push origin master

}

docker_build() {
    echo "Construindo container"
    docker build -t leafarlins/$SITENAME:v$VERSAO .
    docker build -t leafarlins/$SITENAME:latest .
    docker push leafarlins/$SITENAME:v$VERSAO
    docker push leafarlins/$SITENAME:latest
}

VERSAO=$1
HOJE=$(date "+%Y-%m-%d")
SITENAME="site"

echo "Building version $VERSAO"

docker_build
edit_changelog
commit_tag

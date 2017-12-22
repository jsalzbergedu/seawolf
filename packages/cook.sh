#!/bin/bash
# Inspired by redox' cook.sh
set -e
OP="$1"
PKG="$2"
touch .cookvars
source .cookvars
# Orange and unorange
ORN='\033[1;33m'
URN='\033[0m'
# Bold and unbold

# Colored echo
cecho() {
    echo -e "${ORN}$1${URN}"
}

usage() {
    echo "cook.sh <option> <package>" >&2
    echo "        download"
    echo "        deps" >&2
    echo "        redeps" >&2
    echo "        build" >&2
    echo "        rebuild" >&2
    echo "        clean" >&2
    echo "        install" >&2
}

if [ "x$OP" = "x" ] && [ "x$PKG" = "x" ]
then
    usage
    exit 1
fi

# Necessary before any other task
download() {
    git clone https://github.com/jsalzbergedu/swpackages.git
    echo "SW_PACKAGES_DOWNLOADED" >> cookvars
    echo "Seawolf packages downloaded"
}


# Archlinux
arch_deps() {
    if [ -d opencv2]
    then
	rm -r opencv2
    fi
    git clone https://aur.archlinux.org/opencv2.git
    pushd opencv2
    makepkg -si
    popd
    echo "DEPS_INSTALLED=1" >> cookvars
    cecho "Installed dependancies"
}

arch_build_onepkg() {
    pkgdir="$1"
    cecho "Building package $pkgdir"
    pushd "$pkgdir"
    for dir in *
    do
	echo
	cecho "Building subdir $dir"
	pushd "$dir"
	makepkg
	popd
    done
    popd
    cecho "Built $pkgdir"
}

arch_build() {
    pushd swpackages
    pushd arch
    if [ "$1" = "all" ]
    then
	for pkg in *
	do
	    arch_build_onepkg "$pkg"
	done
    else
	arch_build_onepkg "$1"
    fi
    popd
    popd
}

arch_clean_onepkg() {
    pkgdir="$1"
    cecho "Cleaning package $pkgdir"
    pushd "$pkgdir"
    for dir in *
    do
	cecho "Cleaning subdir $dir"
	pushd "$dir"
	for file in *
	do
	    if [ ! "$file" = "PKGBUILD" ]
	    then
		rm -rf "$file"
	    fi
	done
	popd
    done
    popd
}

arch_clean() {
    pushd swpackages
    pushd arch
    if [ "$1" = "all" ]
    then
	for pkg in *
	do
	    arch_clean_onepkg "$pkg"
	done
    else
	arch_clean_onepkg "$1"
    fi
    popd
    popd
}


arch_install_onepkg() {
    pkgdir="$1"
    cecho "Installing package $pkgdir"
    pushd "$pkgdir"
    for dir in *
    do
	cecho "Installing subdir $dir"
	pushd "$dir"
	makepkg -si
	popd
    done
    popd
}

arch_install() {
    pushd swpackages
    pushd arch
    if [ "$1" = "all" ]
    then
	for pkg in *
	do
	    arch_install_onepkg "$pkg"
	done
    else
	arch_install_onepkg "$1"
    fi
    popd
    popd
}

# Placeholders for the real functions
DEPS_FN=""
BUILD_FN=""
CLEAN_FN=""
INSTALL_FN=""

redeps() {
    $DEPS_FN $@
}

deps() {
    if [ $DEPS_INSTALLED ]
    then
	cecho "Deps already installed"
    else
	redeps $@
    fi
}

build() {
    $BUILD_FN $@
}

clean() {
    $CLEAN_FN $@
}

rebuild() {
    clean $@
    build $@
}

install() {
    deps $@
    clean $@
    build $@
    $INSTALL_FN $@
}

# Set the correct functions depending on os
source /etc/os-release 
OS="$ID"
if [ "$OS" = "arch" ]
then
    DEPS_FN="arch_deps"
    BUILD_FN="arch_build"
    CLEAN_FN="arch_clean"
    INSTALL_FN="arch_install"
else
    echo "OS or distro either unsupported or without packages"
    exit 1
fi

cook() {
    OP="$1"
    PKG="$2"
    case "$OP" in
	download)
	    download
	    ;;
	deps)
	    deps
	    ;;
	redeps)
	    redeps
	    ;;
	build)
	    build "$PKG"
	    ;;
	clean)
	    clean "$PKG"
	    ;;
	install)
	    install "$PKG"
	    ;;
	--help)
	    usage
	    ;;
	-h)
	    usage
	    ;;
	*)
	    cecho "${OP}: Command not recognized" >&2
	    usage
	    ;;
    esac
}

cook $@

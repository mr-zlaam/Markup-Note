#!/bin/sh
case "$1" in
    *[Uu]sername*)
        echo "${MARKUP_NOTES_GIT_USER:-oauth2}"
        ;;
    *)
        echo "${MARKUP_NOTES_GIT_TOKEN}"
        ;;
esac

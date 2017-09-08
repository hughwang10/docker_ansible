#!/bin/sh
cp tmp/site_spec/* site_spec
cp tmp/vars/* vars
chown -R miepadm:miepgrp site_spec
chown -R miepadm:miepgrp vars
chmod -x vars/*-hosts
/bin/bash tmp/miit_cmd.sh

# Copyright (c) 2015 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# sum core makefile

# The name of the application to be built
APP = sum

# Directory to create APLX files in (must include trailing slash)
APP_OUTPUT_DIR = ../binaries/

SOURCE_DIRS = .
SOURCES = sum.c comms_s.c process_s.c init_s.c

LIBRARIES += -lm
CFLAGS += -Wno-shift-negative-value

# The GFE application standard makefile
include $(SPINN_DIRS)/make/local.mk

all: $(APP_OUTPUT_DIR)$(APP).aplx

# Tidy up
tidy:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt

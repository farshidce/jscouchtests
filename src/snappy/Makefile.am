## Licensed under the Apache License, Version 2.0 (the "License"); you may not
## use this file except in compliance with the License. You may obtain a copy of
## the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
## WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
## License for the specific language governing permissions and limitations under
## the License.

snappyebindir = $(localerlanglibdir)/snappy-1.0.3/ebin
snappyprivdir = $(localerlanglibdir)/snappy-1.0.3/priv

if WINDOWS
SNAPPY_OUTPUT_DIR = win32
snappy_msbuild = $(SNAPPY_OUTPUT_DIR)/msbuild.bat
snappy_vcproj = $(SNAPPY_OUTPUT_DIR)/snappy.vcxproj
WIN_ERL_INCLUDE = $(SNAPPY_OUTPUT_DIR)/win_erl_include.tmp
SNAPPY_NIF = $(SNAPPY_OUTPUT_DIR)/snappy_nif.dll
endif

snappy_cxx_srcs = \
	snappy_nif.cc \
	google-snappy/snappy.cc \
	google-snappy/snappy-sinksource.cc \
	google-snappy/snappy-stubs-internal.cc

snappy_cxx_hdrs = \
	erl_nif_compat.h \
	google-snappy/snappy.h \
	google-snappy/snappy-internal.h \
	google-snappy/snappy-sinksource.h \
	google-snappy/snappy-stubs-internal.h \
	google-snappy/snappy-stubs-public.h

snappy_file_collection = \
    snappy.app.in \
    snappy.erl

snappyebin_make_generated_file_list = \
    snappy.app \
    snappy.beam

EXTRA_DIST = \
	$(snappy_cxx_hdrs) \
    $(snappy_file_collection)

CLEANFILES = \
    $(snappyebin_make_generated_file_list) \
	priv/snappy_nif.so

snappyebin_DATA = \
    $(snappyebin_make_generated_file_list)

if !WINDOWS
if USE_OTP_NIFS
snappypriv_LTLIBRARIES = snappy_nif.la
snappy_nif_la_SOURCES = $(snappy_cxx_srcs)
snappy_nif_la_LDFLAGS = -module -avoid-version

priv/snappy_nif.so: snappy_nif.la
	@mkdir -p ./priv
	cp .libs/snappy_nif.so $@

all: priv/snappy_nif.so
endif
endif

if WINDOWS
$(SNAPPY_NIF) : $(snappy_msbuild) $(snappy_vcproj)
	$(MKDIR_P) "$(snappyprivdir)" || true
	(cd win32 && ./msbuild.bat)
	cp $(SNAPPY_NIF) $(snappyprivdir)

all: $(SNAPPY_NIF)

$(snappy_msbuild): $(snappy_msbuild).tpl
	sed -e "s|%msbuild_dir%|$(msbuild_dir)|" \
	    -e "s|%msbuild_name%|$(msbuild_name)|" \
	    -e "s|^/cygdrive/\([a-zA-Z]\)|\1:|" \
	< $< > $@

$(snappy_vcproj): $(snappy_vcproj).tpl $(WIN_ERL_INCLUDE)
	 sed -e "s|%ERLANG_INCLUDE%|`cat $(WIN_ERL_INCLUDE)`|" \
	< $< > $@

$(WIN_ERL_INCLUDE):$(ERLANG_INCLUDE)
	echo $< | sed -e "s|^/cygdrive/\([a-zA-Z]\)|\1:|" > $@
endif

%.app: %.app.in
	cp $< $@

%.beam: %.erl
	$(ERLC) $(ERLC_FLAGS) $<

.PHONY: \
	clean \
	coverage \
	deb

# Note that this target is run during deb packaging.
.DEFAULT: noop

noop:
	@echo Nothing to do!

clean:
	rm -rf debian/process-control*
	rm -f debian/files
	rm -f debian/debhelper-build-stamp

coverage:
	nosetests --with-coverage --cover-package=processcontrol --cover-html
	@echo Results are in cover/index.html

deb: debian
	@echo Note that this is not how we build our production .deb
	# FIXME: fragile
	cd ..; tar cjf process-control_1.0.6.orig.tar.bz2 process-control; cd process-control
	debuild -us -uc

debian:
	@[ ! -d debian ] && (echo You can clone the debian directory from https://github.com/adamwight/process-control-debian ; exit 1)

.PHONY: \
	coverage \
	deb

# Note that this target is run during deb packaging.
.DEFAULT: noop

noop:
	@echo Nothing to do!

coverage:
	nosetests --with-coverage --cover-package=processcontrol --cover-html
	@echo Results are in cover/index.html

deb:
	@echo Note that this is not how we build our production .deb
	# FIXME: fragile
	cd ..; tar cjf process-control_0.0.1~rc1.orig.tar.bz2 process-control; cd process-control
	debuild -us -uc

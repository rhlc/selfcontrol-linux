VERSION := $(shell cat ../VERSION)
SRCDIR  := $(abspath ..)

.PHONY: deb rpm arch clean

deb:
	cd deb && bash build-deb.sh $(VERSION) $(SRCDIR)

rpm:
	rpmbuild -bb \
		--define "_topdir $(CURDIR)/rpm/rpmbuild" \
		--define "version $(VERSION)" \
		--define "srcdir $(SRCDIR)" \
		rpm/selfcontrol-linux.spec
	@echo "RPM written to rpm/rpmbuild/RPMS/"

arch:
	cd arch && VERSION=$(VERSION) SRCDIR=$(SRCDIR) makepkg -f
	@echo "Arch package written to arch/"

clean:
	rm -rf deb/build deb/*.deb
	rm -rf rpm/rpmbuild
	rm -rf arch/pkg arch/src arch/*.pkg.tar.*

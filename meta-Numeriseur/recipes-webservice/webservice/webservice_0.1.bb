DESCRIPTION = "Microphone script "
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://${OPENSTLINUX_BASE}/files/licenses/ST-Proprietary;md5=7cb1e55a9556c7dd1a3cae09db9cc85f"


FILESEXTRAPATHS_prepend := "${THISDIR}:"

SRC_URI = "\
		file://webservice.py \
		file://webservice-load.service \
		file://config_web \
		"



inherit systemd
do_configure[noexec] = "1"
do_compile[noexec] = "1"



do_install() {
	
	install -d ${D}${bindir}/numeriseur/webservice
	install -d ${D}${bindir}/numeriseur/webservice/config_web
	install -d ${D}${sysconfdir}/init.d/
	install -d ${D}${systemd_unitdir}/system
	
    install -m 0755 ${WORKDIR}/webservice.py ${D}${bindir}/numeriseur/webservice/webservice.py
    install -m 0755 ${WORKDIR}/webservice.py ${D}${sysconfdir}/init.d/webservice.py
    install -c -m 0644 ${WORKDIR}/webservice-load.service ${D}${systemd_unitdir}/system
    cp  -rf ${WORKDIR}/config_web/* ${D}${bindir}/numeriseur/webservice/config_web



}



FILES_${PN} += "${sysconfdir}/init.d ${systemd_unitdir}/system"
FILES_${PN} += "${bindir}/numeriseur/webservice/"

SYSTEMD_SERVICE_${PN} = "webservice-load.service"
SYSTEMD_AUTO_ENABLE_${PN} = "enable"
INITSCRIPT_NAME= "webservice.py"


RDEPENDS_${PN} += "python3 python3-django python3-psutil python3-configparser"




SUMMARY = "Recette du microphone d'ambiance cabine"
DESCRIPTION = "recette permettant de transmettre en temps réel les flux audio du cab radio par RTSP"
SECTION = "numeriseur"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://setup.py \
           file://main_microphone.py \
           file://utils \
           file://microphone-load.service \
           file://utils/__init__.py "


S = "${WORKDIR}"

DEPENDS += "python3-cython-native"
inherit systemd setuptools3  python3native distutils3

do_install_append () {

	install -d ${D}${sysconfdir}/init.d/
	install -d ${D}${systemd_unitdir}/system
    install -d ${D}${bindir}


    install -m 0755 main_microphone.py ${D}${bindir}
    install -m 0755 ${WORKDIR}/main_microphone.py ${D}${sysconfdir}/init.d/main_microphone.py

    install -c -m 0644 ${WORKDIR}/microphone-load.service ${D}${systemd_unitdir}/system

}

FILES_${PN} += "${sysconfdir}/init.d ${systemd_unitdir}/system"

SYSTEMD_SERVICE_${PN} = "microphone-load.service"
SYSTEMD_AUTO_ENABLE_${PN} = "enable"
INITSCRIPT_NAME= "main_microphone.py"


RDEPENDS_${PN} = "\
		  python3 \
		  python3-pyaudio \
		  python3-netifaces \
		  python3-cython \
		  python3-setuptools \
		  python3-typing-extensions \
		  python-typing \
		"
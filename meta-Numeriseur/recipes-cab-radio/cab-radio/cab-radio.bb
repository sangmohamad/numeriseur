DESCRIPTION = "Python script "
SECTION = "numeriseur"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"



S = "${WORKDIR}"

SRC_URI = "\
		file://cab-radio.py \
		file://Config.ini \
		file://numeriseur-load.service \
		file://speech_data \
		file://utils \
		file://setup.py \
		"




inherit systemd setuptools3  python3native  distutils3

BBCLASSEXTEND = "native"


do_install_append () {
	
	install -d ${D}${bindir}/numeriseur
	install -d ${D}${bindir}/numeriseur/stm32
	install -d ${D}${bindir}/numeriseur/stm32/speech_data
	install -d ${D}${sysconfdir}/init.d/
	install -d ${D}${systemd_unitdir}/system
    

    install -m 0755 ${WORKDIR}/cab-radio.py ${D}${bindir}/numeriseur/stm32/cab-radio.py
    install -m 0755 ${WORKDIR}/Config.ini   ${D}${bindir}/numeriseur/stm32/Config.ini
    install -m 0755 ${WORKDIR}/cab-radio.py ${D}${sysconfdir}/init.d/cab-radio.py

 
  	cp  -rf ${WORKDIR}/speech_data/* ${D}${bindir}/numeriseur/stm32/speech_data/
    install -c -m 0644 ${WORKDIR}/numeriseur-load.service ${D}${systemd_unitdir}/system

    	
	


}



FILES_${PN} += "${sysconfdir}/init.d ${systemd_unitdir}/system"
FILES_${PN} += "${bindir}/numeriseur/"
FILES_${PN}-userfs = "${bindir}/numeriseur/"
FILES_${PN} += "${prefix}/bin/"
PACKAGES += "${PN}-userfs"

SYSTEMD_SERVICE_${PN} = "numeriseur-load.service"
SYSTEMD_AUTO_ENABLE_${PN} = "enable"
INITSCRIPT_NAME= "cab-radio.py"


RDEPENDS_${PN} += "python3 python3-pyaudio python3-requests  python3-pocketsphinx python3-configparser python3-django python3-psutil  python3-numpy  python3-scipy python3-periphery "

DEPENDS += "python3-cython-native"
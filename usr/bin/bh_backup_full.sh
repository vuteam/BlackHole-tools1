#!/bin/sh
###############################################################################
#                      FULL BACKUP UYILITY FOR  VU+                           #
#        Tools original by scope34 with additions by Dragon48 & DrData        #
#               modified by Pedro_Newbie (pedro.newbie@gmail.com)             #
#                       modified by meo & dpeddi                              #
###############################################################################

getaddr() {
	python - $1 $2<<-"EOF"
		from sys import argv
		filename = argv[1]
		address = int(argv[2])
		fh = open(filename,'rb')
		header = fh.read(2048)
		fh.close()
		print "%d" % ( (ord(header[address+2]) <<16 ) | (ord(header[address+1]) << 8) |  ord(header[address]) )
	EOF
}

START=$(date +%s)

if [ $# = 0 ]; then
	echo "Error: missing target device specification"
	echo "       mount the target device from blue panel before running this tool"
	exit
fi

DIRECTORY=$1
DATE=`date +%Y%m%d_%H%M`
IMAGEVERSION=`date +%Y%m%d`

# TESTING FOR UBIFS
if grep rootfs /proc/mounts | grep ubifs > /dev/null; then
	ROOTFSTYPE=ubifs
	MKUBIFS_ARGS="-m 2048 -e 126976 -c 4096 -F"
	UBINIZE_ARGS="-m 2048 -p 128KiB"
else
# NO UBIFS THEN JFFS2
	ROOTFSTYPE=jffs2
	MTDROOT=0
	MTDBOOT=2
	JFFS2OPTIONS="--eraseblock=0x20000 -n -l"
fi

MKFS=/usr/sbin/mkfs.$ROOTFSTYPE
UBINIZE=/usr/sbin/ubinize
NANDDUMP=/usr/sbin/nanddump
WORKDIR=$DIRECTORY/bi
TARGET="XX"

if [ -f /proc/stb/info/vumodel ] ; then
	MODEL=$( cat /proc/stb/info/vumodel )
	TYPE=VU
	SHOWNAME="Vu+ ${MODEL}"
	MAINDEST=$DIRECTORY/vuplus/${MODEL}
	EXTRA=$DIRECTORY/fullbackup_${MODEL}/$DATE/vuplus	
else
	echo "No supported receiver found!"
	exit 0
fi

## START THE REAL BACK-UP PROCESS
echo "$SHOWNAME" | tr  a-z A-Z
echo "BACK-UP TOOL, FOR MAKING A COMPLETE BACK-UP"
echo " "
echo "Please be patient, ... will take about 5-7 minutes for this system."
echo " "

## TESTING IF ALL THE TOOLS FOR THE BUILDING PROCESS ARE PRESENT
if [ ! -f $MKFS ] ; then
	echo $MKFS; echo "not found."
	exit 0
fi
if [ ! -f $NANDDUMP ] ; then
	echo $NANDDUMP ;echo "not found."
	exit 0
fi

## PREPARING THE BUILDING ENVIRONMENT
rm -rf $WORKDIR
mkdir -p $WORKDIR
mkdir -p /tmp/bi/root
sync
mount --bind / /tmp/bi/root

unset REBOOT_UPDATE
unset FORCE_UPDATE
unset ROOTFSDUMP_FILENAME
unset KERNELDUMP_FILENAME
unset SPLASHDUMP_FILENAME

KERNELDUMP_MODE=nanddump
SPLASHDUMP_MODE=nanddump
INITRDDUMP_MODE=nanddump


echo " "
echo "Cleaning target directory!"

rm -rf $MAINDEST
mkdir -p $MAINDEST
#mkdir -p $EXTRA/${MODEL}

case ${MODEL} in
	solo2)
		ROOTFS_EXT=bin
		INITRD=initrd_cfe_auto.bin
		REBOOT_UPDATE=yes
	;;
	duo2)
		ROOTFS_EXT=bin
		INITRD=initrd_cfe_auto.bin
		REBOOT_UPDATE=yes
	;;
	solose)
		ROOTFS_EXT=bin
		INITRD=initrd_cfe_auto.bin
		FORCE_UPDATE=yes
	;;
	zero)
		ROOTFS_EXT=bin
		INITRD=initrd_cfe_auto.bin
		FORCE_UPDATE=yes
	;;
	solo4k)
		REBOOT_UPDATE=yes
		BKLDEV=/dev/mmcblk0
		KERNELDUMP_MODE=dd
		SPLASHDUMP_MODE=dd
		INITRDDUMP_MODE=dd
		ROOTFSTYPE=tar.bz2

		KERNELDUMP_FILENAME=kernel_auto.bin
		SPLASHDUMP_FILENAME=splash_auto.bin
		INITRDDUMP_FILENAME=initrd_auto.bin
		ROOTFSDUMP_FILENAME=rootfs.tar.bz2
	;;
	*)
		ROOTFS_EXT=jffs2
	;;
esac

[[ -z ${KERNELDUMP_FILENAME} ]] && KERNELDUMP_FILENAME=kernel_cfe_auto.bin
[[ -z ${SPLASHDUMP_FILENAME} ]] && SPLASHDUMP_FILENAME=splash_cfe_auto.bin
[[ -z ${ROOTFSDUMP_FILENAME} ]] && ROOTFSDUMP_FILENAME=root_cfe_auto.${ROOTFS_EXT}

## DUMP ROOTFS
case $ROOTFSTYPE in
    jffs2)
	echo "Create: root.jffs2"
	$MKFS --root=/tmp/bi/root --faketime --output=$WORKDIR/root.$ROOTFSTYPE $JFFS2OPTIONS
    ;;
    ubifs)
	echo "Create: root.ubifs"
	echo \[ubifs\] > $WORKDIR/ubinize.cfg
	echo mode=ubi >> $WORKDIR/ubinize.cfg
	echo image=$WORKDIR/root.ubi >> $WORKDIR/ubinize.cfg
	echo vol_id=0 >> $WORKDIR/ubinize.cfg
	echo vol_type=dynamic >> $WORKDIR/ubinize.cfg
	echo vol_name=rootfs >> $WORKDIR/ubinize.cfg
	echo vol_flags=autoresize >> $WORKDIR/ubinize.cfg
	touch $WORKDIR/root.ubi
	chmod 644 $WORKDIR/root.ubi
	#cp -ar /tmp/bi/root $WORKDIR/root
	#$MKFS -r $WORKDIR/root -o $WORKDIR/root.ubi $MKUBIFS_ARGS
	$MKFS -r /tmp/bi/root -o $WORKDIR/root.ubi $MKUBIFS_ARGS || rm $WORKDIR/root.ubi
	$UBINIZE -o $WORKDIR/root.$ROOTFSTYPE $UBINIZE_ARGS $WORKDIR/ubinize.cfg || rm $WORKDIR/root.$ROOTFSTYPE
    ;;
    tar.bz2)
	tar -jcf $WORKDIR/root.$ROOTFSTYPE -C /tmp/bi/root . || rm $WORKDIR/root.$ROOTFSTYPE
    ;;
esac
chmod 644 $WORKDIR/root.$ROOTFSTYPE
mv $WORKDIR/root.$ROOTFSTYPE $MAINDEST/${ROOTFSDUMP_FILENAME} || rm $MAINDEST/${ROOTFSDUMP_FILENAME}

echo "Create: kerneldump"
case ${KERNELDUMP_MODE} in
	dd)
		DDDEV=$(sfdisk -d ${BKLDEV} | sed -n '/name="kernel"/s/ :.*//p')
		dd if=${DDDEV} of=$WORKDIR/kernel.dump || rm $WORKDIR/kernel.dump
		#dd if=kernel.dump bs=1 count=4 skip=44 (46 45 44) -->size
	;;
	*)
		kernelmtd=$(cat /proc/mtd  | grep kernel | cut -d\: -f1)
		nanddump /dev/$kernelmtd -q > $WORKDIR/kernel.dump || rm $WORKDIR/kernel.dump
	;;
esac
#mv $WORKDIR/kernel.dump $MAINDEST/${KERNELDUMP_FILENAME} || rm $MAINDEST/${KERNELDUMP_FILENAME}
ADDR=$(getaddr $WORKDIR/kernel.dump 44)
dd if=$WORKDIR/kernel.dump of=$MAINDEST/$KERNELDUMP_FILENAME bs=$ADDR count=1 && rm $WORKDIR/kernel.dump || rm $MAINDEST/$KERNELDUMP_FILENAME

##DUMP SPLASH
echo "Create: splashdump"
case ${SPLASHDUMP_MODE} in
	dd)
		DDDEV=$(sfdisk -d ${BKLDEV} | sed -n '/name="splash"/s/ :.*//p')
		dd if=${DDDEV} of=$WORKDIR/splash.dump || rm $WORKDIR/splash.dump
		#543 -->size
		#mv $WORKDIR/kernel_auto.bin || rm $MAINDEST/kernel_auto.bin
	;;
	*)
		splashmtd=$(cat /proc/mtd  | grep splash | cut -d\: -f1)
		if [ x$splashmtd != x ]; then
			nanddump /dev/$splashmtd -q > $WORKDIR/splash.dump || rm $WORKDIR/splash.dump
		fi
	;;
esac
if [ -s $WORKDIR/splash.dump ]; then
	DOWNLOADSPLASH=0
	#mv $WORKDIR/splash.dump $MAINDEST/$SPLASHDUMP_FILENAME || rm $MAINDEST/$SPLASHDUMP_FILENAME
	ADDR=$(getaddr $WORKDIR/splash.dump 2)
	dd if=$WORKDIR/splash.dump of=$MAINDEST/$SPLASHDUMP_FILENAME bs=$ADDR count=1 && rm $WORKDIR/splash.dump || rm $MAINDEST/$SPLASHDUMP_FILENAME
else
	echo "dump not possible, splash will be downloaded later"
	DOWNLOADSPLASH=1
fi

##DUMP INITRD
echo "Create: initrddump"
case ${INITRDDUMP_MODE} in
	dd)
		DDDEV=$(sfdisk -d ${BKLDEV} | sed -n '/name="initrd"/s/ :.*//p')
		dd if=${DDDEV} of=$WORKDIR/initrd.dump || rm $WORKDIR/initrd.dump
	;;
	#*)
	#	splashmtd=$(cat /proc/mtd  | grep splash | cut -d\: -f1)
	#	if [ x$splashmtd != x ]; then
	#		nanddump /dev/$splashmtd -q > $WORKDIR/splash.dump || rm $WORKDIR/splash.dump
	#	fi
	#;;
esac

if [ -s $WORKDIR/initrd.dump ]; then
	DOWNLOADINTRD=0
	#mv $WORKDIR/initrd.dump $MAINDEST/${INITRDDUMP_FILENAME} || rm $MAINDEST/${INITRDDUMP_FILENAME}
	ADDR=$(getaddr $WORKDIR/initrd.dump 44)
	dd if=$WORKDIR/initrd.dump of=$MAINDEST/$INITRDDUMP_FILENAME bs=$ADDR count=1 && rm $WORKDIR/initrd.dump || rm $MAINDEST/$INITRDDUMP_FILENAME
else
    echo "dump not possible, splash will be downloaded later"
	DOWNLOADINTRD=1
fi



	if [[ $DOWNLOADINTRD = 1 || $DOWNLOADSPLASH = 1 ]]; then
		case ${MODEL} in
		duo2|solo2|solose|zero)
			echo "Vu+ ${MODEL} don't expose some partitions, try getting it from internet"
			mkdir -p /tmp/backupfull-$$
			cd /tmp/backupfull-$$ && \
			opkg update && \
			opkg download vuplus-bootlogo && \
			ar x vuplus-bootlogo* && \
			tar zxvf data.tar.gz
			if [[ $DOWNLOADINTRD = 1 ]]; then
			    find . -name "initrd_cfe_auto.bin" -exec mv {} $MAINDEST/$INITRD \; 
			fi
			if [[ $DOWNLOADSPLASH = 1 ]]; then
			    find . -name "splash_cfe_auto.bin" -exec mv {} $MAINDEST/$SPLASHDUMP_FILENAME \; 
			fi
			cd - > /dev/null
			rm -rf /tmp/backupfull-$$
		;;
		esac
	fi

	if [ x$REBOOT_UPDATE = xyes ]; then
		touch $MAINDEST/reboot.update
		chmod 664 $MAINDEST/reboot.update
	fi

	if [ x$FORCE_UPDATE = xyes ]; then
		touch $MAINDEST/force.update
		chmod 664 $MAINDEST/force.update
	fi

	#cp -r $MAINDEST $EXTRA #copy the made back-up to images
	if [ -f $MAINDEST/${ROOTFSDUMP_FILENAME} -a -f $MAINDEST/${KERNELDUMP_FILENAME} ]; then
		echo " "
		echo "USB Image created in:";echo $MAINDEST
		#echo "# and there is made an extra copy in:"
		#echo $EXTRA
		echo " "
		echo "To restore the image:"
		echo "Place the USB-flash drive in the (front) USB-port and switch the receiver off and on with the powerswitch on the back of the receiver."
		echo "Follow the instructions on the front-display."
		echo "Please wait.... almost ready!"

	else
		echo "Image creation FAILED!"
		echo "Probable causes could be:"
		echo "-> no space left on back-up device"
		echo "-> no writing permission on back-up device"
		echo " "
	fi

umount /tmp/bi/root
rmdir /tmp/bi/root
rmdir /tmp/bi
rm -rf $WORKDIR
sleep 5
END=$(date +%s)
DIFF=$(( $END - $START ))
MINUTES=$(( $DIFF/60 ))
SECONDS=$(( $DIFF-(( 60*$MINUTES ))))
echo "Time required for this process:" ; echo "$MINUTES:$SECONDS"
exit 
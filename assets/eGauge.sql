-- ----------------------------
-- egauge database
-- ----------------------------

CREATE DATABASE IF NOT EXISTS `eGauge`;
USE `eGauge`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for egauge
-- ----------------------------
DROP TABLE IF EXISTS `egauge`;
CREATE TABLE `egauge` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(64) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `data` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for upload_status
-- ----------------------------
DROP TABLE IF EXISTS `upload_status`;
CREATE TABLE `upload_status` (
  `id` tinyint(4) NOT NULL AUTO_INCREMENT,
  `table_name` varchar(20) NOT NULL,
  `device_id` varchar(64) DEFAULT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP,
  `last_uploaded_datetime` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

SET FOREIGN_KEY_CHECKS = 1;

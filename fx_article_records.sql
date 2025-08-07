/*
 Navicat Premium Dump SQL

 Source Server         : local_mysql
 Source Server Type    : MySQL
 Source Server Version : 80043 (8.0.43)
 Source Host           : localhost:3306
 Source Schema         : xuanfa

 Target Server Type    : MySQL
 Target Server Version : 80043 (8.0.43)
 File Encoding         : 65001

 Date: 05/08/2025 22:12:36
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for fx_article_records
-- ----------------------------
DROP TABLE IF EXISTS `fx_article_records`;
CREATE TABLE `fx_article_records`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `crawl_time` datetime NOT NULL COMMENT '爬取时间',
  `crawl_channel` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '爬取渠道（官网、微信公众号等）',
  `unit_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '单位名称',
  `article_title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '文章标题',
  `article_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '文章内容',
  `publish_time` datetime NULL DEFAULT NULL COMMENT '文章发布时间',
  `view_count` int NULL DEFAULT NULL COMMENT '浏览次数',
  `article_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '文章链接',
  `article_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '文章ID（来源系统中的唯一标识）',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `update_time` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 64 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文章记录表' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

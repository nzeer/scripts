-- inventory_schema.sql
--
-- Additive schema for nmap discovery + gathered Ansible facts.
--
-- inventory_discovery is intentionally independent of inventory_hosts:
-- every nmap-discovered IPv4 address gets a row even when SSH/fact gathering
-- fails and no ./hosts/<hostname> YAML file exists.

CREATE DATABASE IF NOT EXISTS inventory
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE inventory;


CREATE TABLE IF NOT EXISTS inventory_hosts (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    hostname            VARCHAR(255) NOT NULL,
    fqdn                VARCHAR(255) NULL,

    os_distribution     VARCHAR(128) NULL,
    os_major_version    VARCHAR(32) NULL,
    os_minor_version    VARCHAR(32) NULL,
    os_full_version     VARCHAR(64) NULL,

    source_file         VARCHAR(255) NULL,
    facts_json          JSON NOT NULL,

    first_seen          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_inventory_hosts_hostname (hostname),
    KEY idx_inventory_hosts_fqdn (fqdn),
    KEY idx_inventory_hosts_os (
        os_distribution,
        os_major_version,
        os_minor_version
    ),
    KEY idx_inventory_hosts_last_seen (last_seen)
) ENGINE=InnoDB;


-- Lightweight record for EVERY discovered IPv4 address.
--
-- host_id is NULL until/if a gathered fact file can associate this IP with a
-- full inventory_hosts record.
--
-- currently_discovered answers:
--   "Did the latest nmap-derived inventory contain this IP?"
--
-- facts_available answers:
--   "Did the current load have gathered host facts for this IP?"
CREATE TABLE IF NOT EXISTS inventory_discovery (
    id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ipv4_address            VARCHAR(45) NOT NULL,
    host_id                 BIGINT UNSIGNED NULL,
    discovery_source        VARCHAR(64) NOT NULL DEFAULT 'nmap',

    currently_discovered    BOOLEAN NOT NULL DEFAULT TRUE,
    facts_available         BOOLEAN NOT NULL DEFAULT FALSE,

    first_seen              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_inventory_discovery_ipv4 (ipv4_address),
    KEY idx_inventory_discovery_host (host_id),
    KEY idx_inventory_discovery_current (currently_discovered),
    KEY idx_inventory_discovery_facts (facts_available),
    KEY idx_inventory_discovery_last_seen (last_seen),

    CONSTRAINT fk_inventory_discovery_host
        FOREIGN KEY (host_id)
        REFERENCES inventory_hosts(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS inventory_addresses (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    host_id             BIGINT UNSIGNED NOT NULL,
    ipv4_address        VARCHAR(45) NOT NULL,
    mac_address         VARCHAR(32) NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_inventory_addresses_host_ip_mac (
        host_id,
        ipv4_address,
        mac_address
    ),
    KEY idx_inventory_addresses_ipv4 (ipv4_address),
    KEY idx_inventory_addresses_mac (mac_address),

    CONSTRAINT fk_inventory_addresses_host
        FOREIGN KEY (host_id)
        REFERENCES inventory_hosts(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- Canonical reference table for non-empty /etc/humangroups entries.
CREATE TABLE IF NOT EXISTS inventory_tags (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tag_name            VARCHAR(512) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_inventory_tags_name (tag_name)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS inventory_host_tags (
    host_id             BIGINT UNSIGNED NOT NULL,
    tag_id              BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (host_id, tag_id),
    KEY idx_inventory_host_tags_tag (tag_id),

    CONSTRAINT fk_inventory_host_tags_host
        FOREIGN KEY (host_id)
        REFERENCES inventory_hosts(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_inventory_host_tags_tag
        FOREIGN KEY (tag_id)
        REFERENCES inventory_tags(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- Main future-web-UI view. This intentionally starts from discovery rather
-- than inventory_hosts so unreachable/no-SSH systems still appear.
CREATE OR REPLACE VIEW inventory_discovery_summary AS
SELECT
    d.id AS discovery_id,
    d.ipv4_address,
    d.currently_discovered,
    d.facts_available,
    d.discovery_source,
    d.first_seen AS discovery_first_seen,
    d.last_seen AS discovery_last_seen,

    h.id AS host_id,
    h.hostname,
    h.fqdn,
    h.os_distribution,
    h.os_major_version,
    h.os_minor_version,
    h.os_full_version,
    h.source_file,
    h.last_seen AS facts_last_seen,

    (
        SELECT COUNT(*)
        FROM inventory_host_tags ht
        WHERE ht.host_id = h.id
    ) AS tag_count

FROM inventory_discovery d
LEFT JOIN inventory_hosts h
    ON h.id = d.host_id;


CREATE OR REPLACE VIEW inventory_host_summary AS
SELECT
    h.id,
    h.hostname,
    h.fqdn,
    h.os_distribution,
    h.os_major_version,
    h.os_minor_version,
    h.os_full_version,
    h.source_file,
    h.first_seen,
    h.last_seen,
    h.updated_at,
    COUNT(DISTINCT a.id) AS address_count,
    COUNT(DISTINCT ht.tag_id) AS tag_count
FROM inventory_hosts AS h
LEFT JOIN inventory_addresses AS a
    ON a.host_id = h.id
LEFT JOIN inventory_host_tags AS ht
    ON ht.host_id = h.id
GROUP BY
    h.id,
    h.hostname,
    h.fqdn,
    h.os_distribution,
    h.os_major_version,
    h.os_minor_version,
    h.os_full_version,
    h.source_file,
    h.first_seen,
    h.last_seen,
    h.updated_at;
 

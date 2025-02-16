// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

//  owner constrcutor

contract Locker {
    struct Info {
        string recipient_name;
        bool valid;
        address validater_addr;
        string validater_name;
        uint timestamp;
    }

    // this holds the map with hash of file and struct containing needed info
    mapping(bytes => Info) private Records;

    address private owner;

    constructor() {
        // Set the transaction sender as the owner of the contract.
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier cheakduplicate(bytes memory _file_hash) {
        require(Records[_file_hash].timestamp == 0, "Record Already Exists");
        _;
    }

    function addData(
        bytes memory _file_hash,
        string memory _r_name,
        address _val_addr,
        string memory _val_name,
        bool _valid
    ) public onlyOwner() cheakduplicate(_file_hash) {
        Records[_file_hash] = Info({
            recipient_name: _r_name,
            valid: _valid,
            validater_addr: _val_addr,
            validater_name: _val_name,
            timestamp: block.timestamp
        });
    }

    function getData(
        bytes memory _file_hash
    ) public view returns (Info memory) {
        return Records[_file_hash];
    }

    // Function to update file information
    function updateData(
        bytes memory _fileHash,
        string memory _r_name,
        string memory _val_name,
        address _val_addr,
        bool _valid
    ) public {
        require(bytes(Records[_fileHash].recipient_name).length != 0, "Record does not exist."); // Ensure the record exists
        Records[_fileHash].recipient_name = _r_name;
        Records[_fileHash].validater_name = _val_name;
        Records[_fileHash].valid = _valid;
        Records[_fileHash].validater_addr = _val_addr;
        //Records[_fileHash].timestamp = block.timestamp;
    }

    // Function to delete file information
    function deleteData(bytes memory _fileHash) public {
        require(bytes(Records[_fileHash].recipient_name).length != 0, "Record does not exist."); // Ensure the record exists
        delete Records[_fileHash];
    }
}

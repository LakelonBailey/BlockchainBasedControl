// SPDX-License-Identifier: MIT
pragma solidity ^0.5.0;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v2.5.1/contracts/token/ERC20/ERC20.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v2.5.1/contracts/token/ERC20/ERC20Detailed.sol";

contract MyEnergyToken is ERC20, ERC20Detailed {
    constructor(uint256 initialSupply) public ERC20Detailed("EnergyToken", "ETK", 18) {
        _mint(msg.sender, initialSupply * (10 ** uint256(decimals())));
    }
}
// SPDX-License-Identifier: MIT
pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

contract EnergyOrderBookNativeCurrency {

    struct Order {
        address user;
        uint256 energyAmount; // in kWh
        uint256 pricePerUnit; // tokens per kWh
        bool isBuy; // true = buy, false = sell
        bool isMarket;
        bytes32 orderId;
    }

    Order[] public buyOrders;
    Order[] public sellOrders;

    uint256 public lastTradedPrice;

    mapping(bytes32 => uint256) public buyOrderIndex;
    mapping(bytes32 => uint256) public sellOrderIndex;
    mapping(address => uint256) public balances;

    event OrderPlaced(address indexed user, bool isBuy, uint256 amount, uint256 pricePerUnit, bytes32 orderId, bool market);
    event OrderCancelled(address indexed user, bool isBuy, uint256 index, bytes32 oid);
    event OrderMatched(address indexed buyer, bytes32 buyerOrderId, address indexed seller, bytes32 sellerOrderId, uint256 energyAmount, uint256 pricePerUnit, uint256 cost);

    constructor() public {
        balances[msg.sender] = 1_000_000; // Creator gets 1M units
    }

    function getBestBid() public view returns (uint256) {
        return buyOrders.length > 0 ? buyOrders[0].pricePerUnit : 0;
    }

    function getBestAsk() public view returns (uint256) {
        return sellOrders.length > 0 ? sellOrders[0].pricePerUnit : 0;
    }

    function getBuyOrders() public view returns (Order[] memory) {
        return buyOrders;
    }

    function getSellOrders() public view returns (Order[] memory) {
        return sellOrders;
    }

    function getPrice() public view returns (uint256 bestBid, uint256 bestAsk, uint256 lastPrice) {
        bestBid = buyOrders.length > 0 ? buyOrders[0].pricePerUnit : 0;
        bestAsk = sellOrders.length > 0 ? sellOrders[0].pricePerUnit : 0;
        lastPrice = lastTradedPrice;
    }
    
    function getBalance(address user) public view returns (uint256) {
        return balances[user];
    }

    function insertBuyOrder(Order memory newOrder) internal {
        uint i = 0;
        while(i < buyOrders.length && newOrder.pricePerUnit <= buyOrders[i].pricePerUnit){ i++; }
        buyOrders.push(newOrder);
        for(uint j = buyOrders.length-1; j > i; j--){
            buyOrders[j] = buyOrders[j-1];
            buyOrderIndex[buyOrders[j].orderId] = j;
        }
        buyOrders[i] = newOrder;
        buyOrderIndex[newOrder.orderId] = i;
    }

    function insertSellOrder(Order memory newOrder) internal {
        uint i = 0;
        while(i < sellOrders.length && newOrder.pricePerUnit >= sellOrders[i].pricePerUnit){ i++; }
        sellOrders.push(newOrder);
        for(uint j = sellOrders.length-1; j > i; j--){
            sellOrders[j] = sellOrders[j-1];
            sellOrderIndex[sellOrders[j].orderId] = j;
        }
        sellOrders[i] = newOrder;
        sellOrderIndex[newOrder.orderId] = i;
    }

    function removeSellOrder(uint256 ind) internal {
        require(ind < sellOrders.length, "Index out of bounds");
        bytes32 removedOrderId = sellOrders[ind].orderId;
        for(uint256 i = ind; i < sellOrders.length-1; i++){
            sellOrders[i] = sellOrders[i+1];
            sellOrderIndex[sellOrders[i].orderId] = i;
        }
        sellOrders.pop();
        delete sellOrderIndex[removedOrderId];
    }

    function removeBuyOrder(uint256 ind) internal {
        require(ind < buyOrders.length, "Index out of bounds");
        bytes32 removedOrderId = buyOrders[ind].orderId;
        for(uint256 i = ind; i < buyOrders.length-1; i++){
            buyOrders[i] = buyOrders[i+1];
            buyOrderIndex[buyOrders[i].orderId] = i;
        }
        buyOrders.pop();
        delete buyOrderIndex[removedOrderId];
    }

    function matchOrderBuy(Order memory newOrder) internal {
        require(newOrder.isBuy, "Must be a buy order");
        for(uint i = 0; i < sellOrders.length && newOrder.energyAmount > 0; i++){
            Order storage sell = sellOrders[i];
            if(newOrder.isMarket || newOrder.pricePerUnit >= sell.pricePerUnit){

                uint256 tradableAmount = sell.energyAmount > newOrder.energyAmount ? newOrder.energyAmount : sell.energyAmount;
                uint256 cost = tradableAmount * sell.pricePerUnit;

                require(balances[newOrder.user] >= cost, "Insufficient balance");
                balances[newOrder.user] -= cost;
                balances[sell.user] += cost;

               
                emit OrderMatched(newOrder.user, newOrder.orderId, sell.user, sell.orderId, tradableAmount, sell.pricePerUnit, cost);

                lastTradedPrice = sell.pricePerUnit;
                sell.energyAmount -= tradableAmount;
                newOrder.energyAmount -= tradableAmount;
                if(sell.energyAmount == 0){ removeSellOrder(i); i--; }
            }
        }
        if(newOrder.energyAmount > 0 && !newOrder.isMarket){ insertBuyOrder(newOrder); }
    }

    function matchOrderSell(Order memory newOrder) internal {
        require(!newOrder.isBuy, "Must be a sell order");
        for(uint i = 0; i < buyOrders.length && newOrder.energyAmount > 0; i++){
            Order storage buy = buyOrders[i];
            if(newOrder.isMarket || newOrder.pricePerUnit <= buy.pricePerUnit){
                uint256 tradableAmount = buy.energyAmount > newOrder.energyAmount ? newOrder.energyAmount : buy.energyAmount;
                uint256 cost = tradableAmount * buy.pricePerUnit;
                require(balances[buy.user] >= cost, "Buyer balance insufficient");
                balances[buy.user] -= cost;
                balances[newOrder.user] += cost;
                
                
                emit OrderMatched(buy.user, buy.orderId, newOrder.user, newOrder.orderId, tradableAmount, buy.pricePerUnit, cost);
                lastTradedPrice = buy.pricePerUnit;
                buy.energyAmount -= tradableAmount;
                newOrder.energyAmount -= tradableAmount;
                if(buy.energyAmount == 0){ removeBuyOrder(i); i--; }
            }
        }
        if(newOrder.energyAmount > 0 && !newOrder.isMarket){ insertSellOrder(newOrder); }
    }


    function cancelOrder(bytes32 orderId, bool isBuy) public {
        if (isBuy) {
            uint index = buyOrderIndex[orderId];
            require(index < buyOrders.length, "Invalid index");
            require(buyOrders[index].user == msg.sender, "Not your order");
            removeBuyOrder(index);
            delete buyOrderIndex[orderId];
            emit OrderCancelled(msg.sender, true, index, orderId);
        } else {
            uint index = sellOrderIndex[orderId];
            require(index < sellOrders.length, "Invalid index");
            require(sellOrders[index].user == msg.sender, "Not your order");
            removeSellOrder(index);
            delete sellOrderIndex[orderId];
            emit OrderCancelled(msg.sender, false, index, orderId);
        }
    }
    
    function removeAllOrdersForUser(address user) public {
        require(msg.sender == user, "Unauthorized");

        // Remove buy orders (backwards)
        for (uint i = buyOrders.length; i > 0; i--) {
            if (buyOrders[i - 1].user == user) {
                removeBuyOrder(i - 1);
            }
        }

        // Remove sell orders (backwards)
        for (uint j = sellOrders.length; j > 0; j--) {
            if (sellOrders[j - 1].user == user) {
                removeSellOrder(j - 1);
            }
        }
    }

    function placeOrder(uint256 energyAmount, uint256 pricePerUnit, bool isBuy, bool isMarket) public {
        if (balances[msg.sender] == 0) {
            balances[msg.sender] = 1_000_000; // First-time users get initial balance
        }

        bytes32 orderId = keccak256(abi.encodePacked(msg.sender, now, energyAmount, pricePerUnit, isBuy));
        Order memory newOrder = Order(msg.sender, energyAmount, pricePerUnit, isBuy, isMarket, orderId);

        if (isBuy) {
            if(newOrder.energyAmount > 0){
                matchOrderBuy(newOrder);
            }
        } else {
            if(newOrder.energyAmount > 0){
                matchOrderSell(newOrder);
            }
        }

        emit OrderPlaced(msg.sender, isBuy, energyAmount, pricePerUnit, orderId, isMarket);
    }
}
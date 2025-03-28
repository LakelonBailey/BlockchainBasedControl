
// SPDX-License-Identifier: MIT
pragma solidity ^0.5.0;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v2.5.1/contracts/token/ERC20/ERC20.sol";
pragma experimental ABIEncoderV2;



contract EnergyOrderBook{

    struct Order {
        address user;
        uint256 energyAmount; // in kWh
        uint256 pricePerUnit; // token per kWh
        bool isBuy; // true = buy, false = sell
        bool isMarket;
        bytes32 orderId;
    }

    Order[] public buyOrders;
    Order[] public sellOrders;

    uint256 public lastTradedPrice;

    mapping(bytes32 => uint256) public buyOrderIndex;
    mapping(bytes32 => uint256) public sellOrderIndex;

    ERC20 public token;    


    event OrderPlaced(address indexed user, bool isBuy, uint256 amount, uint256 pricePerUnit, bytes32 orderId);
    event OrderCancelled(address indexed user, bool isBuy, uint256 index);
    event OrderMatched(address indexed buyer, bytes32 buyerOrderId, address indexed seller, bytes32 sellerOrderId, uint256 energyAmount, uint256 pricePerUnit, uint256 cost);
    //event OrderPartiallyFilled(address indexed buyer, bytes32 buyerOrderId, address indexed seller, bytes32 sellerOrderId, uint256 energyAmount, uint256 pricePerUnit);


    constructor(address tokenAddress) public {
        token = ERC20(tokenAddress);
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




    function removeSellOrder(uint256 ind) internal {
        require(ind < sellOrders.length, "Index out of bounds");
        //shift index to front and pop
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
        //shift index to front and pop
        bytes32 removedOrderId = buyOrders[ind].orderId;

        for(uint256 i = ind; i < buyOrders.length-1; i++){
            buyOrders[i] = buyOrders[i+1];
            buyOrderIndex[buyOrders[i].orderId] = i;
        }
        buyOrders.pop();
        delete buyOrderIndex[removedOrderId];
    }


    function matchMarketOrderBuy(Order memory newOrder) internal {
        require(newOrder.isBuy && newOrder.isMarket, "Must be a market buy order");

        //fill from the top | does not go into order book
        //loop through sell orders
        for(uint i = 0; i < sellOrders.length && newOrder.energyAmount > 0; i++){
            Order storage sell = sellOrders[i];

            if(newOrder.pricePerUnit >= sellOrders[i].pricePerUnit){
                //transaction happens 
                // entire order 
                uint256 tradableAmount = sell.energyAmount > newOrder.energyAmount ? newOrder.energyAmount : sell.energyAmount;
                uint256 cost = tradableAmount * sell.pricePerUnit;

                require(token.transferFrom(newOrder.user, sell.user, cost), "Payment failed");
                emit OrderMatched(newOrder.user, newOrder.orderId, sell.user, sell.orderId, tradableAmount, sell.pricePerUnit, cost);
                lastTradedPrice = sell.pricePerUnit;

                sell.energyAmount -= tradableAmount;
                newOrder.energyAmount -= tradableAmount;

                if(sell.energyAmount == 0){
                    removeSellOrder(i);
                    i--; //it shifts so reset i
                } 
                
            }
        }

    }


    function matchMarketOrderSell(Order memory newOrder) internal {
        require(!newOrder.isBuy && newOrder.isMarket, "Must be a market sell order");
        //fill from the top | does not go into order book
        //loop through buy orders
        for(uint i = 0; i < buyOrders.length && newOrder.energyAmount > 0; i++){
            Order storage buy = buyOrders[i];
            if (newOrder.pricePerUnit <= buyOrders[i].pricePerUnit) {
                //transaction happens 
                uint256 tradableAmount = buy.energyAmount > newOrder.energyAmount ? newOrder.energyAmount : buy.energyAmount;
                uint256 cost = tradableAmount * buy.pricePerUnit;
                
                require(token.transferFrom(buy.user, newOrder.user, cost), "Payment failed");
                emit OrderMatched(buy.user, buy.orderId, newOrder.user, newOrder.orderId, tradableAmount, buy.pricePerUnit, cost);
                lastTradedPrice = buy.pricePerUnit;
                buy.energyAmount -= tradableAmount;
                newOrder.energyAmount -= tradableAmount;
                if(buy.energyAmount == 0){
                    removeBuyOrder(i);
                    i--; //it shifts so reset i
                } 
            }
        }

    }

    function matchOrders() internal {
        uint256 i = 0;
        while (i < buyOrders.length) {
            uint256 j = 0;
            while (j < sellOrders.length) {
                Order storage selectBuy = buyOrders[i];
                Order storage selectSell = sellOrders[j];

                if (selectBuy.pricePerUnit >= selectSell.pricePerUnit) {
                    uint256 tradableAmount = selectBuy.energyAmount > selectSell.energyAmount ? selectSell.energyAmount : selectBuy.energyAmount;
                    uint256 cost = tradableAmount * selectSell.pricePerUnit;

                    // Token transfer: from buyer to seller
                    require(token.transferFrom(selectBuy.user, selectSell.user, cost), "Payment failed");
                    emit OrderMatched(selectBuy.user, selectBuy.orderId, selectSell.user, selectSell.orderId, tradableAmount, selectSell.pricePerUnit, cost);
                    lastTradedPrice = selectSell.pricePerUnit;
                    selectBuy.energyAmount -= tradableAmount;
                    selectSell.energyAmount -= tradableAmount;

                    if (selectSell.energyAmount == 0) {
                        removeSellOrder(j);
                        // Don't increment j; array has shifted
                        continue;
                    }
                    if (selectBuy.energyAmount == 0) {
                        removeBuyOrder(i);
                        // Go to next buy order
                        i--;
                        break;
                    }
                }
                j++;
            }
            i++;
        }
    }

    function insertBuyOrder(Order memory newOrder) internal {
        //First sort by price 
        uint i = 0;
        while(i < buyOrders.length && newOrder.pricePerUnit <= buyOrders[i].pricePerUnit){
            i++;
        }
        buyOrders.push(newOrder);
        //inserted element is at J needs to be shifted to position
        for(uint j = buyOrders.length-1; j < i; j--){
            buyOrders[j] = buyOrders[j-1];
            buyOrderIndex[buyOrders[j].orderId] = j;
        }
        buyOrders[i] = newOrder;
        buyOrderIndex[newOrder.orderId] = i;
        //Last sort by time 
    }

    function insertSellOrder(Order memory newOrder) internal {
        //First sort by price 
        uint i = 0;
        while(i < sellOrders.length && newOrder.pricePerUnit >= sellOrders[i].pricePerUnit){
            i++;
        }
        sellOrders.push(newOrder);
        //inserted element is at J needs to be shifted to position
        for(uint j = sellOrders.length-1; j < i; j--){
            sellOrders[j] = sellOrders[j-1];
            sellOrderIndex[sellOrders[j].orderId] = j;
        }
        sellOrders[i] = newOrder;
        sellOrderIndex[newOrder.orderId] = i;
    }

    function cancelOrder(bytes32 orderId, bool isBuy) public {
        if (isBuy) {
            uint index = buyOrderIndex[orderId];
            require(index < buyOrders.length, "Invalid index");
            require(buyOrders[index].user == msg.sender, "Not your order");
            removeBuyOrder(index);
            delete buyOrderIndex[orderId];
            emit OrderCancelled(msg.sender, true, index);
        } else {
            uint index = sellOrderIndex[orderId];
            require(index < sellOrders.length, "Invalid index");
            require(sellOrders[index].user == msg.sender, "Not your order");
            removeSellOrder(index);
            delete sellOrderIndex[orderId];
            emit OrderCancelled(msg.sender, false, index);
        }
    }


    function placeOrder(uint256 energyAmount, uint256 pricePerUnit, bool isBuy, bool isMarket) public {
        bytes32 orderId = keccak256(abi.encodePacked(msg.sender, now, energyAmount, pricePerUnit, isBuy));
        Order memory newOrder = Order(msg.sender, energyAmount, pricePerUnit, isBuy, isMarket, orderId);

        if(isMarket){
            if(isBuy){
                matchMarketOrderBuy(newOrder);
            }
            else{
                matchMarketOrderSell(newOrder);
            }
            emit OrderPlaced(msg.sender, isBuy, energyAmount, pricePerUnit, orderId);

        }
        else{
            if(isBuy){
                insertBuyOrder(newOrder);
            }   else {
                insertSellOrder(newOrder);
            }
            emit OrderPlaced(msg.sender, isBuy, energyAmount, pricePerUnit, orderId);
            matchOrders();
        }


    }

}


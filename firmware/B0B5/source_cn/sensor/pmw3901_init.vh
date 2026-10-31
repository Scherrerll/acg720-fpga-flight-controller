// PMW3901 性能寄存器初始化常量表，来源为 Bitcraze 上游驱动，完整保留 73 项及原次序。
// 本文件由 flow_reader.v 在 init_rom 声明后包含；每项 16 位，高 8 位地址、低 8 位写入值。
// 地址 0x7F 选择寄存器页，其他地址的含义随页而变；不得跨页重排或删除重复写入。
// 本表只提供上电初值；SPI 发送及等待由 flow_reader 主状态机完成，其中索引 58 后等待 100 ms。
initial begin
    // 前段按页依次装载性能参数；每次 0x7F 写入都保留页切换边界。
    init_rom[0] = 16'h7F00;
    init_rom[1] = 16'h61AD;
    init_rom[2] = 16'h7F03;
    init_rom[3] = 16'h4000;
    init_rom[4] = 16'h7F05;
    init_rom[5] = 16'h41B3;
    init_rom[6] = 16'h43F1;
    init_rom[7] = 16'h4514;
    init_rom[8] = 16'h5B32;
    init_rom[9] = 16'h5F34;
    init_rom[10] = 16'h7B08;
    init_rom[11] = 16'h7F06;
    init_rom[12] = 16'h441B;
    init_rom[13] = 16'h40BF;
    init_rom[14] = 16'h4E3F;
    init_rom[15] = 16'h7F08;
    init_rom[16] = 16'h6520;
    init_rom[17] = 16'h6A18;
    init_rom[18] = 16'h7F09;
    init_rom[19] = 16'h4FAF;
    init_rom[20] = 16'h5F40;
    init_rom[21] = 16'h4880;
    init_rom[22] = 16'h4980;
    init_rom[23] = 16'h5777;
    init_rom[24] = 16'h6078;
    init_rom[25] = 16'h6178;
    init_rom[26] = 16'h6208;
    init_rom[27] = 16'h6350;
    init_rom[28] = 16'h7F0A;
    init_rom[29] = 16'h4560;
    init_rom[30] = 16'h7F00;
    init_rom[31] = 16'h4D11;
    init_rom[32] = 16'h5580;
    init_rom[33] = 16'h741F;
    init_rom[34] = 16'h751F;
    init_rom[35] = 16'h4A78;
    init_rom[36] = 16'h4B78;
    init_rom[37] = 16'h4408;
    init_rom[38] = 16'h4550;
    init_rom[39] = 16'h64FF;
    init_rom[40] = 16'h651F;
    init_rom[41] = 16'h7F14;
    init_rom[42] = 16'h6560;
    init_rom[43] = 16'h6608;
    init_rom[44] = 16'h6378;
    init_rom[45] = 16'h7F15;
    init_rom[46] = 16'h4858;
    // 中段切到页 7/页 0x10 完成设置；索引 58 写入后由调用方执行长等待。
    init_rom[47] = 16'h7F07;
    init_rom[48] = 16'h410D;
    init_rom[49] = 16'h4314;
    init_rom[50] = 16'h4B0E;
    init_rom[51] = 16'h450F;
    init_rom[52] = 16'h4442;
    init_rom[53] = 16'h4C80;
    init_rom[54] = 16'h7F10;
    init_rom[55] = 16'h5B02;
    init_rom[56] = 16'h7F07;
    init_rom[57] = 16'h4041;
    init_rom[58] = 16'h7000;
    // 长等待后的收尾写入，最终回到页 0 并完成剩余性能配置。
    init_rom[59] = 16'h3244;
    init_rom[60] = 16'h7F07;
    init_rom[61] = 16'h4040;
    init_rom[62] = 16'h7F06;
    init_rom[63] = 16'h62F0;
    init_rom[64] = 16'h6300;
    init_rom[65] = 16'h7F0D;
    init_rom[66] = 16'h48C0;
    init_rom[67] = 16'h6FD5;
    init_rom[68] = 16'h7F00;
    init_rom[69] = 16'h5BA0;
    init_rom[70] = 16'h4EA8;
    init_rom[71] = 16'h5A50;
    init_rom[72] = 16'h4080;
end

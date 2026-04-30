#include <stdint.h>
namespace DeepLr {
#pragma pack(push,1)
	struct WebSocketHeader {
		int32_t version;//版本号
		int32_t code;//信息类型
		int32_t length;//实际内容长度
	};
#pragma pack(pop)

}
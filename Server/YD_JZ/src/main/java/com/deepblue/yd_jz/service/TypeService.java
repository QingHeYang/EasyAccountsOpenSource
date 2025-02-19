package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.TypeSingleDto;
import com.deepblue.yd_jz.dto.TypeListResponseDto;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class TypeService {

    private static final Logger log = LoggerFactory.getLogger(TypeService.class);
    @Autowired
    TypeRepository typeRepository;

    @Autowired
    FlowTemplateService flowTemplateService;

    @Transactional(rollbackFor = Exception.class)
    public void addType(TypeSingleDto typeSingleDto) {
        Type type = new Type();
        type.setTName(typeSingleDto.getTName());
        type.setParent(typeSingleDto.getParent());
        type.setParent(typeSingleDto.getParent() == null ? -1 : typeSingleDto.getParent());
        type.setActionId(typeSingleDto.getActionId());
        type.setAnalysisDisable(typeSingleDto.getAnalysisDisable());
        typeRepository.save(type);
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateType(TypeSingleDto typeSingleDto) {
        Type type = new Type();
        type.setId(typeSingleDto.getId());
        type.setTName(typeSingleDto.getTName());
        type.setAnalysisDisable(typeSingleDto.getAnalysisDisable());
        if (typeSingleDto.getParent() == null) {
            type.setParent(-1);
        } else {
            type.setParent(typeSingleDto.getParent());
        }
        if ((typeSingleDto.getParent() == null || typeSingleDto.getParent() == -1) ) {
            List<Type> typeList = typeRepository.findByParent(typeSingleDto.getId());
            if (typeSingleDto.getActionId() != null) {
                for (Type t : typeList) {
                    t.setActionId(typeSingleDto.getActionId());
                    typeRepository.save(t);
                }
            }
            if (typeSingleDto.getAnalysisDisable()!=null){
                for (Type t : typeList) {
                    t.setAnalysisDisable(typeSingleDto.getAnalysisDisable());
                    typeRepository.save(t);
                }
            }
        }
        type.setActionId(typeSingleDto.getActionId());
        typeRepository.save(type);
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableType(int id) {
        typeRepository.findById(id).ifPresent(type -> {
            type.setDisable(true);
            typeRepository.save(type);
            flowTemplateService.clearType(id);
            if (type.getParent() == -1) {
                typeRepository.findByParent(id).forEach(childType -> {
                    childType.setDisable(true);
                    typeRepository.save(childType);
                    flowTemplateService.clearType(childType.getId());
                });
            }
        });
    }

    @Transactional(rollbackFor = Exception.class)
    public void archiveType(int id, boolean archive) {
        typeRepository.findById(id).ifPresent(type -> {
            type.setArchive(archive);
            typeRepository.save(type);
            flowTemplateService.clearType(id);
            if (type.getParent() == -1) {
                typeRepository.findByParentNoLimit(id).forEach(childType -> {
                    childType.setArchive(archive);
                    typeRepository.save(childType);
                    flowTemplateService.clearType(childType.getId());
                });
            }
        });
    }

    @Transactional(rollbackFor = Exception.class)
    public List<Type> queryTypeList(int parent) {
        List<Type> typeList = typeRepository.findByParent(parent);
        log.info("typeList: " + typeList);
        return typeRepository.findByParent(parent);
    }

    @Transactional(rollbackFor = Exception.class)
    public Type queryTypeSingle(int id) {
        return typeRepository.findById(id).orElse(null);
    }

    @Transactional(rollbackFor = Exception.class)
    public Type queryTypeParent(int id) {
        Type type = typeRepository.findById(id).orElse(null);
        if (type == null) {
            return null;
        }
        return typeRepository.findById(type.getParent()).orElse(null);
    }

    @Transactional(rollbackFor = Exception.class)
    public List<TypeListResponseDto> queryAllType(boolean limit) {
        List<Type> allTypes = limit ? typeRepository.findAllTypes() : typeRepository.findAll();
        List<TypeListResponseDto> toClients = new ArrayList<>();
        for (Type type : allTypes) {
            if (type.getParent() == -1) {
                TypeListResponseDto typeListResponseDto = new TypeListResponseDto();
                typeListResponseDto = typeListResponseDto.convertToDto(type);
                toClients.add(typeListResponseDto);
            }
        }
        for (Type type : allTypes) {
            if (type.getParent() != -1) {
                TypeListResponseDto child = new TypeListResponseDto();
                child = child.convertToDto(type);

                for (TypeListResponseDto parent : toClients) {
                    if (parent.getId() == child.getParent()) {
                        if (parent.getChildrenTypes() == null) {
                            List<TypeListResponseDto> children = new ArrayList<>();
                            parent.setChildrenTypes(children);
                        }
                        parent.getChildrenTypes().add(child);
                    }
                }
            }
        }
        return toClients;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<TypeListResponseDto> queryTypeByActionId(int actionId) {
        List<Type> allTypes = typeRepository.findByActionIdOrNull(actionId);
        List<TypeListResponseDto> toClients = new ArrayList<>();
        for (Type type : allTypes) {
            if (type.getParent() == -1) {
                TypeListResponseDto typeListResponseDto = new TypeListResponseDto();
                typeListResponseDto.convertToDto(type);
                toClients.add(typeListResponseDto);
            }
        }

        for (Type type : allTypes) {
            if (type.getParent() != -1) {
                TypeListResponseDto child = new TypeListResponseDto();
                child.convertToDto(type);

                for (TypeListResponseDto parent : toClients) {
                    if (parent.getId() == child.getParent()) {
                        if (parent.getChildrenTypes() == null) {
                            List<TypeListResponseDto> children = new ArrayList<>();
                            parent.setChildrenTypes(children);
                        }
                        parent.getChildrenTypes().add(child);
                    }
                }
            }
        }

        //此处逻辑存疑，应该是有逻辑冲突，部分功能，可能是快记模板 与流水之间的冲突
        /*Iterator<TypeListResponseDto> iterator = toClients.iterator();
        while (iterator.hasNext()) {
            TypeListResponseDto type = iterator.next();
            if (type.getChildrenTypes() == null || type.getChildrenTypes().isEmpty()) {
                iterator.remove();
            }
        }*/

        return toClients;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<TypeListResponseDto> queryTypeArchive() {
        List<Type> allTypes = typeRepository.findTypesByArchive();
        Map<Integer, TypeListResponseDto> dtoMap = new HashMap<>();
        List<TypeListResponseDto> rootTypes = new ArrayList<>();

        // 首先为所有类型创建 DTO 并存入 map 中
        for (Type type : allTypes) {
            TypeListResponseDto dto = new TypeListResponseDto();
            dto.convertToDto(type);
            dtoMap.put(type.getId(), dto);
        }

        // 构建父子关系
        for (Type type : allTypes) {
            TypeListResponseDto currentDto = dtoMap.get(type.getId());
            if (type.getParent() == -1) {
                rootTypes.add(currentDto);
            } else {
                TypeListResponseDto parentDto = dtoMap.get(type.getParent());
                if (parentDto != null) {
                    if (parentDto.getChildrenTypes() == null) {
                        parentDto.setChildrenTypes(new ArrayList<>());
                    }
                    parentDto.getChildrenTypes().add(currentDto);
                } else {
                    // 如果没有找到父节点，将其作为根节点处理
                    rootTypes.add(currentDto);
                }
            }
        }
        return rootTypes;
    }

}
